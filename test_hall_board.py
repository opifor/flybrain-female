"""Twelve distinct door cards share the healthy rooms."""
from collections import Counter
import asyncio
import json
import random
from dataclasses import replace

import pytest
import hall
import musicroom
import paintroom
from test_rooms import Health, make_room, registry
from test_betroom import FakePage, IMG


@pytest.mark.parametrize('count', [0, 1, 2, 3, 4])
def test_spread_previews_and_shuffle(tmp_path, count):
    rooms = registry()
    rooms.register(musicroom.DECLARATION, 'http://127.0.0.1:4674')
    rooms.register(paintroom.DECLARATION, 'http://127.0.0.1:4676')
    rooms.rooms = dict(list(rooms.rooms.items())[:count])
    for path in rooms.rooms:
        directory = tmp_path / path.strip('/')
        directory.mkdir()
        cards = [dict(question=f'Question {i}?', title=f'Track {i}', artist=f'Artist {i}') for i in range(12)]
        if path == '/paintroom':
            cards = [dict(name=name) for name in list(paintroom.COLOURS) + list(paintroom.BRUSHES)]
        (directory / 'room.json').write_text(json.dumps({'cards': cards}), encoding='utf-8')
    room = make_room(hall.Hall, tmp_path, registry=rooms, http=Health())
    asyncio.run(room.enter(FakePage([])))
    board = room.board()
    assert len(board['cards']) == (12 if count else 0)
    spread = Counter(c['path'] for c in board['cards'])
    assert spread == {path: 12 // count for path in rooms.rooms}
    assert len({c['token'] for c in board['cards']}) == len(board['cards'])
    for path in rooms.rooms:
        previews = [c['preview'] for c in board['cards'] if c['path'] == path]
        assert len(set(previews)) == len(previews)
        assert set(previews) == {f'Track {i} / Artist {i}' if path == '/musicroom' else
                                 list(paintroom.COLOURS)[i] if path == '/paintroom' else
                                 f'Question {i}?' for i in range(12 // count)}
    expected = list(room._board['cards'])
    random.Random(0).shuffle(expected)
    assert board['cards'] == expected
    if count:
        assert expected != room._board['cards']


def test_same_room_reference_blind_stop_and_mapping(tmp_path):
    rooms = registry()
    rooms.rooms.pop('/tiproom')
    room = make_room(hall.Hall, tmp_path, registry=rooms, http=Health())
    room.refresh_board(force=True)
    cards = room.board()['cards']
    page = FakePage([dict(token=c['token'], x=i * 300, y=0, w=280, h=200) for i, c in enumerate(cards)])
    async def walk():
        await room.enter(page)
        room.pilot.click = True
        for seed in range(4):
            await room.step(page, IMG, 100, 100, seed)
        assert room.destination is None
        assert room.walk_to in {c['token'] for c in cards[1:]}
        await room.step(page, IMG, 400, 100, 4)
        await room.step(page, IMG, 400, 100, 5)
        assert room.destination == '/betroom'
        assert cards[0]['token'] in room._seen
        assert cards[1]['token'] in room._seen
    asyncio.run(walk())


def test_expired_and_unreadable_previews_keep_doors(tmp_path):
    directory = tmp_path / 'betroom'
    directory.mkdir()
    saved = directory / 'room.json'
    room = make_room(hall.Hall, tmp_path, registry=registry(), http=Health())
    for content in ('broken', json.dumps({'cards': [{'question': 'Expired?', 'end_at': 1}]})):
        saved.write_text(content, encoding='utf-8')
        room.refresh_board(force=True)
        assert len(room.board()['cards']) == 12
        assert all(c['preview'] == '' for c in room.board()['cards'])


def test_uneven_spread_and_every_token_maps_to_its_room(tmp_path):
    rooms = registry()
    for i in range(3):
        rooms.register(replace(musicroom.DECLARATION, path=f'/room{i}'), f'http://127.0.0.1:{4674 + i}')
    room = make_room(hall.Hall, tmp_path, registry=rooms, http=Health())
    room.refresh_board(force=True)
    cards = room.board()['cards']
    assert list(Counter(c['path'] for c in room._board['cards']).values()) == [3, 3, 2, 2, 2]
    room._write_look = lambda *args: None
    for card in cards:
        room.destination = None
        room._commit(IMG, 0, 0, 1, card, {}, 0.5, None)
        assert room.destination == card['path']
    room.destination = None
    room._commit(IMG, 0, 0, 1, {'token': '/betroom#99'}, {}, 0.5, None)
    assert room.destination is None
