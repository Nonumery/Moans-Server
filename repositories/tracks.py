import datetime
from typing import List, Optional
from sqlalchemy.dialects.postgresql import aggregate_order_by
from sqlalchemy.orm import selectinload, joinedload, load_only
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Table, and_, delete, or_, insert, literal_column, outerjoin, select, func, update, union_all, desc, exists
from db.tables import LanguageTable, Status, TagTable, TrackTable, UserTable, Voice, trackcheckedtable, tracktagtable, trackseentable
from models.tags import Tag
from models.trackchecked import TrackChecked
from models.tracks import Language, Track, TrackIn, TrackInfo, UserTrack


class TrackRepository:
    # метод для получения информации о треках
    def get_select_track(self, user_id: int, language_id: int, voice: Voice, status: Status, unseen: bool = True, unchecked: bool = True) -> select:
        s = select(TrackTable.id, TrackTable.name, TrackTable.description, TrackTable.path,    # выбор id, наименования, описания, пути

                   func.string_agg(TagTable.tag, aggregate_order_by(
                       literal_column("' '"), TagTable.tag)).label("tags"),  # списка тегов

                   select(func.count()).select_from(select(trackcheckedtable).union_all(select(trackseentable)
                                                                                        .where(~exists(select(trackcheckedtable).filter_by(track_id=trackseentable.c.track_id, user_id=trackseentable.c.user_id)))))
                   # количества лайков
                   .filter_by(liked=True, track_id=TrackTable.id).label("likes"),

                   select(trackcheckedtable.c.liked).filter_by(
                       track_id=TrackTable.id, user_id=user_id, liked=True)  # наличие отметки "понравилось"
                   .union_all(select(trackseentable.c.liked)
                              .filter_by(track_id=TrackTable.id, user_id=user_id, liked=True)).limit(1).label("liked")

                   ).outerjoin(TagTable, TrackTable.tags).where(
            (TrackTable.id.in_(select(trackseentable.c.track_id).filter_by(user_id=user_id)) != unseen
             )
            & (TrackTable.id.in_(select(trackcheckedtable.c.track_id).filter_by(user_id=user_id)) != unchecked
               )).filter(
            TrackTable.user_id != user_id, TrackTable.language_id == language_id, TrackTable.status == status
        ).group_by(TrackTable.id, TrackTable.name, TrackTable.description, TrackTable.path).order_by(desc(TrackTable.created_at))
        if (int(voice.value) == int(Voice.she_he_they.value)):
            return s
        if (int(voice.value) <= int(Voice.they_them.value)):
            voices = [voice, voice.she_he, voice.she_they,
                      voice.he_they, voice.she_he_they]
        else:
            voices = [voice, voice.she_her, voice.he_him,
                      voice.they_them, voice.she_he_they]
        voices.remove(
            Voice(str(int(Voice.she_he_they.value) - int(voice.value) - 1)))
        return s.filter(TrackTable.voice.in_(voices))

    def get_select_liked_tracks(self, user_id: int, unchecked: bool = True) -> select:
        s = select(
            TrackTable.id,
            TrackTable.name,
            TrackTable.description,
            TrackTable.path,
            func.string_agg(TagTable.tag, aggregate_order_by(
                literal_column("' '"), TagTable.tag)).label("tags"),
            select(func.count()).select_from(select(trackcheckedtable).union_all(select(trackseentable).where(~exists(select(trackcheckedtable).filter_by(track_id=trackseentable.c.track_id, user_id=trackseentable.c.user_id))
                                                                                                              ))).filter_by(liked=True, track_id=TrackTable.id).label("likes"),
            select(trackcheckedtable.c.liked).filter_by(track_id=TrackTable.id, user_id=user_id, liked=True
                                                        ).union_all(select(trackseentable.c.liked).filter_by(track_id=TrackTable.id, user_id=user_id, liked=True)).limit(1
                                                                                                                                                                         ).label("liked")
        ).outerjoin(TagTable, TrackTable.tags).where(
            TrackTable.id.in_(select(trackcheckedtable.c.track_id).filter_by(
                user_id=user_id)) != unchecked
        ).filter(
            TrackTable.user_id != user_id
        ).group_by(TrackTable.id, TrackTable.name, TrackTable.description, TrackTable.path).order_by(desc(TrackTable.created_at))
        return s

    def get_select_user_tracks(self, user_id: int) -> select:
        s = select(
            TrackTable.id,
            TrackTable.name,
            TrackTable.status,
            select(func.count()).select_from(select(trackcheckedtable).union_all(select(trackseentable).where(~exists(select(trackcheckedtable).filter_by(track_id=trackseentable.c.track_id, user_id=trackseentable.c.user_id))
                                                                                                              ))).filter_by(liked=True, track_id=TrackTable.id).label("likes")
        ).outerjoin(TagTable, TrackTable.tags).filter(TrackTable.user_id == user_id).group_by(TrackTable.id, TrackTable.name)
        return s

    async def table_to_model(self, session: AsyncSession, user_id: int, name: str) -> Optional[TrackInfo]:
        query = select(TrackTable).options(selectinload(TrackTable.tags)).filter_by(
            name=name).filter_by(user_id=user_id)
        track = (await session.execute(query)).scalar_one()
        track_d = track.__dict__.copy()
        track_d["tags"] = " ".join(t.__dict__["tag"] for t in track.tags)
        q = select(func.count()).select_from(select(trackcheckedtable).union_all(select(trackseentable).where(~exists(select(trackcheckedtable).filter_by(track_id=trackseentable.c.track_id, user_id=trackseentable.c.user_id))
                                                                                                              ))).filter_by(liked=True, track_id=track.id)
        likes = (await session.execute(q)).scalar_one()
        track_d["likes"] = likes
        return TrackInfo.parse_obj(track_d)

    async def get_track_info_by_id(self, session: AsyncSession, id: int) -> Optional[TrackInfo]:
        try:
            query = select(TrackTable).options(
                selectinload(TrackTable.tags)).filter_by(id=id)
            track = (await session.execute(query)).scalar_one()
            track_d = track.__dict__.copy()
            track_d["tags"] = " ".join(t.__dict__["tag"] for t in track.tags)
            q = select(func.count()).select_from(select(trackcheckedtable).union_all(select(trackseentable).where(~exists(select(trackcheckedtable).filter_by(track_id=trackseentable.c.track_id, user_id=trackseentable.c.user_id))
                                                                                                                  ))).filter_by(liked=True, track_id=track.id)
            likes = (await session.execute(q)).scalar_one()
            track_d["likes"] = likes
            return TrackInfo.parse_obj(track_d)
        except exc.NoResultFound:
            print(f"Track {id} is not found")
            return None
        except Exception as e:
            print("get_track_info_by_id", type(e))
            return None

    # метод для получения списка языков
    async def all_langs(self, session: AsyncSession, limit: int = 10, skip: int = 0) -> List[Language]:
        result = await session.execute(select(LanguageTable).limit(limit).offset(skip))
        return [Language.parse_obj(lang.__dict__) for lang in result.scalars().all()]

    async def get_language(self, session: AsyncSession, language_id: int) -> Optional[LanguageTable]:
        try:
            return (await session.execute(select(LanguageTable).where(LanguageTable.id == language_id))).scalars().first()
        except Exception as e:
            print("get_language", type(e))
            return None

    async def get_track(self, session: AsyncSession, user_id: int, name: str) -> Optional[TrackTable]:
        try:
            return (await session.execute(select(TrackTable).where((TrackTable.user_id == user_id) & (TrackTable.name == name)))).scalars().first()
        except Exception as e:
            print("get_track", type(e))
            return None

    async def get_track_by_id(self, session: AsyncSession, id: int) -> Optional[TrackTable]:
        try:
            track = await session.execute(select(TrackTable).filter_by(id=id))
            if not track:
                return None
            return track.scalar_one()
        except exc.NoResultFound as e:
            print(f"Track {id} is not found")
            return None
        except Exception as e:
            print("get_track_by_id", type(e))
            return None
    # метод для получения id пользователя по треку
    # scalar выдает значение|None, а scalar_one() выдает значение|NoResultFound; в случае наличия нескольких строк в обоих случаях выдается исключение MultipleResultsFound

    async def get_user(self, session: AsyncSession, id: int) -> Optional[int]:
        return (await session.execute(select(TrackTable.user_id).filter_by(id=id))).scalar()

    async def get_user_track_by_id(self, session: AsyncSession, user_id: int, track_id: int) -> Optional[TrackInfo]:
        try:
            track = (await session.execute(select(TrackTable).filter_by(id=track_id, user_id=user_id))).scalar_one()
            track_d = track.__dict__
            return await self.table_to_model(session, track_d['user_id'], track_d['name'])
        except exc.NoResultFound as e:
            print(f"Track {track_id} is not found")
            return None
        except Exception as e:
            print("get_user_track_by_id", type(e))
            return None

    def get_voice(self, voice: int):
        try:
            return Voice(voice)
        except Exception as e:
            print("get_voice", type(e))
            return None

    async def check_track(self, session: AsyncSession, track_id: int, user_id: int, liked: bool = False):
        q = insert(trackcheckedtable).values(
            {"track_id": track_id, "user_id": user_id, "liked": liked})
        try:
            await session.execute(q)
            return True
        except exc.IntegrityError as e:
            await session.rollback()
            return False
        except Exception as e:
            print("check_track", type(e))
            await session.rollback()
            return False

    async def view_track(self, session: AsyncSession, track_id: int, user_id: int, liked: bool = False):
        q = insert(trackseentable).values(
            {"track_id": track_id, "user_id": user_id, "liked": liked})
        del_q = delete(trackcheckedtable).where(
            (trackcheckedtable.c.track_id == track_id) & (trackcheckedtable.c.user_id == user_id))
        try:
            await session.execute(del_q)
            await session.execute(q)
            return True
        except Exception as e:
            print("view_track", type(e))
            await session.rollback()
            return False

    async def checks_to_views(self, session: AsyncSession, user_id: int):
        s = select(trackcheckedtable).filter_by(user_id=user_id)
        u = update(trackseentable).values(liked=s.c.liked).filter_by(
            track_id=s.c.track_id, user_id=s.c.user_id)
        s1 = select(trackcheckedtable).filter(~exists().where(trackcheckedtable.c.track_id == trackseentable.c.track_id,
                                                              trackcheckedtable.c.user_id == trackseentable.c.user_id)).filter(trackcheckedtable.c.user_id == user_id)
        i = insert(trackseentable).from_select(
            ['track_id', 'user_id', 'liked'], s1)
        d = delete(trackcheckedtable).filter_by(user_id=user_id)
        try:
            await session.execute(u)
            await session.execute(i)
            await session.execute(d)
            return True
        except Exception as e:
            print("checks_to_views", type(e))
            await session.rollback()
            return False

    async def like_track(self, session: AsyncSession, track_id: int, user_id: int, liked: bool):
        check_query = select(trackcheckedtable).filter(
            trackcheckedtable.c.track_id == track_id, trackcheckedtable.c.user_id == user_id)
        like_query = update(trackcheckedtable).values(liked=liked).where(
            (trackcheckedtable.c.track_id == track_id) & (trackcheckedtable.c.user_id == user_id))
        try:
            if not (await session.execute(check_query)).scalars().first():
                return await self.check_track(session=session, track_id=track_id, user_id=user_id, liked=liked)
            else:
                await session.execute(like_query)
            return True
        except Exception as e:
            print("like_track", type(e))
            await session.rollback()
            return False

    # метод для создания трека
    async def create_new_track(self, session: AsyncSession, user_id: int, path: str, tr: TrackIn, tags_string: str):
        try:
            # обработка полученных тегов
            tags = tags_string.split()
            # исключение возможных повторений
            tags_set = {tag for tag in tags}
            # формирование списка данных трека
            tags_list = (await session.execute(select(TagTable).where(TagTable.tag.in_(tags_set)))).scalars().all()
            exist_tags = [t.tag for t in tags_list]
            not_exist_tags = [t for t in tags_set if t not in exist_tags]
            for tag in not_exist_tags:
                tags_list.append(TagTable(tag=tag))
            track = TrackTable(user_id=int(user_id),
                               language_id=tr.language_id,
                               name=tr.name,
                               description=tr.description,
                               path=path,
                               voice=tr.voice,
                               tags=tags_list)
            self_view = (await session.execute(select(UserTable).filter(UserTable.id == user_id))).scalars().one()
            track.views.append(self_view)
            session.add(track)
            track = await self.get_track(session, track.user_id, track.name)
            trackinfo = await self.table_to_model(session, user_id, track.name)
            return trackinfo

        except Exception as e:
            print("create_new_track", type(e))
            await session.rollback()
            return None

    # метод для редактирования трека
    async def update_track(self, session: AsyncSession, id: int, tr: TrackIn, tags_string: str):
        try:
            # обработка полученных тегов
            tags = tags_string.split()
            # исключение возможных повторений
            tags_set = {tag for tag in tags}
            # формирование списка данных трека
            tags_list = (await session.execute(select(TagTable).where(TagTable.tag.in_(tags_set)))).scalars().all()
            exist_tags = [t.tag for t in tags_list]
            not_exist_tags = [t for t in tags_set if t not in exist_tags]
            for tag in not_exist_tags:
                tags_list.append(TagTable(tag=tag))
            query = select(TrackTable).options(
                selectinload(TrackTable.tags)).filter_by(id=id)
            track = (await session.execute(query)).scalar_one()
            track.name = tr.name
            track.description = tr.description
            track.voice = tr.voice
            track.language_id = tr.language_id
            track.tags = tags_list
            track.status = tr.status
            return await self.table_to_model(session, track.user_id, track.name)
        except Exception as e:
            print("update_track", type(e))
            await session.rollback()
            return None

    # метод для редактирования статуса трека

    async def update_status(self, session: AsyncSession, id: int, status: Status):
        try:
            query = select(TrackTable).filter_by(id=id)
            track = (await session.execute(query)).scalar_one()
            track.status = status
            return await self.table_to_model(session, track.user_id, track.name)
        except Exception as e:
            print("update_status", type(e))
            await session.rollback()
            return None

    # метод для получения списка треков по предпочтениям

    async def get_track_feed(self, session: AsyncSession, user_id: int, language_id: int, voice: Voice, limit: int = 10, skip: int = 0) -> List[TrackInfo]:
        feed_query = union_all(self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=True, unchecked=True),
                               self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=False, unchecked=True)).limit(limit).offset(skip)
        tracks = (await session.execute(feed_query))
        track_list = [{**(TrackInfo.parse_obj(track).dict())}
                      for track in tracks]
        if track_list:
            i = insert(trackcheckedtable).values(
                [{"track_id": i["id"], "user_id": user_id, "liked":i["liked"] if i["liked"] != None else False} for i in track_list])
            await session.execute(i)
        return track_list

    # метод для получения списка треков по предпочтениям
    async def get_track_seen(self, session: AsyncSession, user_id: int, language_id: int, voice: Voice, limit: int = 10, skip: int = 0) -> List[TrackInfo]:
        seen_query = union_all(self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=False, unchecked=True),
                               self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=False, unchecked=False)).limit(limit).offset(skip)
        tracks = (await session.execute(seen_query))
        track_list = [{**(TrackInfo.parse_obj(track).dict())}
                      for track in tracks]
        return track_list

    # метод для получения списка треков по предпочтениям
    async def get_track_liked(self, session: AsyncSession, user_id: int, limit: int = 10, skip: int = 0) -> List[TrackInfo]:
        tracks_query = union_all(
            self.get_select_liked_tracks(user_id=user_id, unchecked=True),
            self.get_select_liked_tracks(user_id=user_id, unchecked=False)
        )
        tr = select(tracks_query.c.id,
                    tracks_query.c.name,
                    tracks_query.c.description,
                    tracks_query.c.path,
                    tracks_query.c.likes,
                    tracks_query.c.liked,
                    tracks_query.c.tags).filter(tracks_query.c.liked == True).limit(limit).offset(skip)
        tracks = (await session.execute(tr))
        track_list = [{**(TrackInfo.parse_obj(track).dict())}
                      for track in tracks]
        return track_list

    # метод для получения списка треков по предпочтениям и по тегам
    async def get_track_feed_with_tags(self, session: AsyncSession, user_id: int, language_id: int, voice: Voice, tags: str, limit: int = 10, skip: int = 0) -> List[TrackInfo]:
        tracks_query = union_all(self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=True, unchecked=True),
                                 self.get_select_track(user_id=user_id, language_id=language_id, voice=voice, status=Status.publish, unseen=False, unchecked=True))
        tr = select(tracks_query.c.id,
                    tracks_query.c.name,
                    tracks_query.c.description,
                    tracks_query.c.path,
                    tracks_query.c.likes,
                    tracks_query.c.liked,
                    tracks_query.c.tags).select_from(tracks_query).where(and_(tracks_query.c['tags'].contains(d) for d in tags.split())).limit(limit).offset(skip)
        tracks = await session.execute(tr)
        track_list = [{**(TrackInfo.parse_obj(track)).dict()}
                      for track in tracks]
        return track_list

    # метод для получения треков по id пользователя
    async def get_user_tracks(self, session: AsyncSession, user_id: int, limit: int = 10, skip: int = 0) -> List[UserTrack]:
        tracks = await session.execute(self.get_select_user_tracks(user_id=user_id).limit(limit).offset(skip))
        track_list = [{**(UserTrack.parse_obj(track)).dict()}
                      for track in tracks]
        return track_list

    # удаление трека
    async def delete_track(self, session: AsyncSession, id: int):
        try:
            track = await self.get_track_by_id(session, id)
            await session.delete(track)
            return True
        except Exception as e:
            print("delete_track", type(e))
            return False
