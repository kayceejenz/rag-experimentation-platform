from psycopg import AsyncConnection
from psycopg.rows import dict_row

from modules.projects.models.project_model import Project, ProjectAccess, ProjectRole


class ProjectRepository:
    FEATURES = ("knowledge", "indexes", "experiments", "benchmarks", "assistants", "runs", "settings")
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def connect(self):
        return await AsyncConnection.connect(self.database_url, row_factory=dict_row)

    @staticmethod
    def project(row) -> Project:
        return Project(
            row["id"],
            row["workspace_id"],
            row["owner_id"],
            row["name"],
            row["description"],
            row["created_at"],
            row["updated_at"],
            bool(row.get("is_default", False)),
        )

    async def create(self, owner_id, name, description):
        async with await self.connect() as db:
            async with db.transaction():
                curr = await db.execute(
                    "insert into ragapp.projects(workspace_id,owner_id,name,description) "
                    "select wm.workspace_id,%s,%s,%s from ragapp.workspace_members wm "
                    "where wm.user_id=%s and wm.role='owner' order by wm.joined_at limit 1 "
                    "returning *",
                    (owner_id, name, description, owner_id),
                )
                row = await curr.fetchone()
                source_cursor = await db.execute(
                    "insert into ragapp.knowledge_bases(project_id,created_by,name) "
                    "values(%s,%s,'Source') returning id",
                    (row["id"], owner_id),
                )
                source = await source_cursor.fetchone()
                await db.execute(
                    "insert into ragapp.project_sources(project_id,knowledge_base_id) values(%s,%s)",
                    (row["id"], source["id"]),
                )
        return self.project(row)

    async def get_access(self, project_id, user_id):
        async with await self.connect() as db:
            curr = await db.execute(
                "select p.*,m.role,(p.id=u.default_project_id) is_default,"
                "(select jsonb_object_agg(acl.feature,jsonb_build_object('view',acl.can_view,'manage',acl.can_manage)) "
                "from ragapp.project_member_permissions acl where acl.project_id=p.id and acl.user_id=m.user_id) permissions "
                "from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "join ragapp.users u on u.id=m.user_id "
                "where p.id=%s and m.user_id=%s and p.deleted_at is null",
                (project_id, user_id),
            )
            row = await curr.fetchone()
        return ProjectAccess(self.project(row), ProjectRole(row["role"]), row["permissions"] or {}) if row else None

    async def list_for_user(self, user_id):
        async with await self.connect() as db:
            curr = await db.execute(
                "select p.*,m.role,(p.id=u.default_project_id) is_default,"
                "(select jsonb_object_agg(acl.feature,jsonb_build_object('view',acl.can_view,'manage',acl.can_manage)) "
                "from ragapp.project_member_permissions acl where acl.project_id=p.id and acl.user_id=m.user_id) permissions "
                "from ragapp.projects p "
                "join ragapp.project_members m on m.project_id=p.id "
                "join ragapp.users u on u.id=m.user_id "
                "where m.user_id=%s and p.deleted_at is null "
                "order by is_default desc,p.updated_at desc",
                (user_id,),
            )
            rows = await curr.fetchall()
        return [ProjectAccess(self.project(row), ProjectRole(row["role"]), row["permissions"] or {}) for row in rows]

    async def update(self, project_id, name, description, update_description):
        async with await self.connect() as db:
            curr = await db.execute(
                "update ragapp.projects set name=coalesce(%s,name), "
                "description=case when %s then %s else description end "
                "where id=%s and deleted_at is null returning *",
                (name, update_description, description, project_id),
            )
            row = await curr.fetchone()
        return self.project(row)

    async def delete(self, project_id):
        async with await self.connect() as db:
            await db.execute("update ragapp.projects set deleted_at=now() where id=%s", (project_id,))

    async def has_permission(self, project_id, user_id, feature, action="view"):
        async with await self.connect() as db:
            row = await (await db.execute(
                "select ragapp.has_project_permission(%s,%s,%s,%s) allowed",
                (project_id, user_id, feature, action),
            )).fetchone()
        return bool(row["allowed"])

    async def list_members(self, project_id):
        async with await self.connect() as db:
            rows = await (await db.execute(
                "select pm.user_id,u.email,u.display_name,pm.role,pm.joined_at,"
                "coalesce(jsonb_object_agg(p.feature,jsonb_build_object('view',p.can_view,'manage',p.can_manage)) "
                "filter(where p.feature is not null),'{}'::jsonb) permissions "
                "from ragapp.project_members pm join ragapp.users u on u.id=pm.user_id "
                "left join ragapp.project_member_permissions p on p.project_id=pm.project_id and p.user_id=pm.user_id "
                "where pm.project_id=%s group by pm.user_id,u.email,u.display_name,pm.role,pm.joined_at "
                "order by (pm.role='owner') desc,lower(coalesce(u.display_name,u.email))",
                (project_id,),
            )).fetchall()
        return rows

    async def add_member(self, project_id, email, permissions):
        async with await self.connect() as db:
            async with db.transaction():
                user = await (await db.execute(
                    "select id from ragapp.users where email=%s and deleted_at is null and is_active",
                    (email,),
                )).fetchone()
                if not user:
                    return None
                inserted = await (await db.execute(
                    "insert into ragapp.project_members(project_id,user_id,role) values(%s,%s,'viewer') "
                    "on conflict do nothing returning user_id",
                    (project_id, user["id"]),
                )).fetchone()
                if not inserted:
                    return False
                await self._replace_permissions(db, project_id, user["id"], permissions)
        return user["id"]

    async def update_member_permissions(self, project_id, member_id, permissions):
        async with await self.connect() as db:
            member = await (await db.execute(
                "select role from ragapp.project_members where project_id=%s and user_id=%s",
                (project_id, member_id),
            )).fetchone()
            if not member or member["role"] == "owner":
                return False
            await self._replace_permissions(db, project_id, member_id, permissions)
        return True

    async def remove_member(self, project_id, member_id):
        async with await self.connect() as db:
            row = await (await db.execute(
                "delete from ragapp.project_members where project_id=%s and user_id=%s and role<>'owner' returning user_id",
                (project_id, member_id),
            )).fetchone()
        return row is not None

    async def _replace_permissions(self, db, project_id, member_id, permissions):
        await db.execute(
            "delete from ragapp.project_member_permissions where project_id=%s and user_id=%s",
            (project_id, member_id),
        )
        for feature in self.FEATURES:
            permission = permissions[feature]
            await db.execute(
                "insert into ragapp.project_member_permissions(project_id,user_id,feature,can_view,can_manage) "
                "values(%s,%s,%s,%s,%s)",
                (project_id, member_id, feature, permission["view"], permission["manage"]),
            )
