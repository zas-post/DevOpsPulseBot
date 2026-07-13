from sqlalchemy import select
from database.connection import async_session
from database.models import Post, PostStatus


async def is_post_exists(source_url: str) -> bool:
    async with async_session() as session:
        stmt = select(Post).where(Post.source_url == source_url)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


async def add_new_post(
    title: str, source_url: str, summary: str, hub_name: str
) -> Post:
    async with async_session() as session:
        new_post = Post(
            title=title,
            source_url=source_url,
            summary=summary,
            hub_name=hub_name,
            status=PostStatus.PENDING,
        )
        session.add(new_post)
        await session.flush()
        await session.commit()
        return new_post


async def get_post_by_id(post_id: int) -> Post:
    async with async_session() as session:
        return await session.get(Post, post_id)


async def update_post_status(post_id: int, new_status: PostStatus) -> None:
    async with async_session() as session:
        post = await session.get(Post, post_id)
        if post:
            post.status = new_status
            await session.commit()


# НОВЫЙ МЕТОД ДЛЯ ОЧЕРЕДИ: Берем 1 самый старый пост в очереди
async def get_next_pending_post() -> Post:
    async with async_session() as session:
        stmt = (
            select(Post)
            .where(Post.status == PostStatus.PENDING)
            .order_by(Post.created_at.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
