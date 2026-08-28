import argparse
import datetime
import json
import mutagen
import os
import pathlib
import requests
import sys
from typing import NotRequired, TypedDict


class Args:
    @staticmethod
    def directory(path: str) -> pathlib.Path:
        if os.path.isdir(path): return pathlib.Path(path)
        raise argparse.ArgumentTypeError(f'{path!r} 不是有效的目录路径。')

    @staticmethod
    def time(t: str) -> datetime.datetime:
        return datetime.datetime.strptime(t, '%Y-%m-%d')

    parser = argparse.ArgumentParser(prog='ynotl', description='ynotlVocadbSongSearcher')
    subparsers = parser.add_subparsers(dest='command', required=True)
    parser_import = subparsers.add_parser('import', help='导入目录')
    parser_import.add_argument('path', help='目录路径', type=directory)
    parser_check = subparsers.add_parser('check', help='检查更新')
    parser_check.add_argument('path', help='目录路径', type=directory)
    parser_check.add_argument('time', default=datetime.datetime.now(), nargs='?',
                              help='YYYY-MM-DD, 仅更新指定日期之前的文件', type=time)
    args = parser.parse_args()


# 常数
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.mp4', '.ape', '.wv', '.aiff', '.aif'}
HEADERS = {'User-Agent': 'ynotl.py/1.0 (contact: 3365139905@qq.com)'}


class FileDataDict(TypedDict):
    id: int
    time: str


class Configure(TypedDict):
    sort: str
    maxResults: int
    search_length_offset: NotRequired[int]
    artist_separator: NotRequired[str]
    album_separator: NotRequired[str]


class DateString:
    @staticmethod
    def load(date_string: str) -> datetime.datetime:
        if '.' in date_string: return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f')
        return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def dump(datetime_obj: datetime.datetime) -> str:
        return datetime_obj.strftime('%Y-%m-%dT%H:%M:%S.%f')


class Request:
    def __init__(self, url, params=None):
        self.run = lambda: requests.get(url, params=params, headers=HEADERS, timeout=10)

    def handle_error(self) -> 'Request':
        original_run = self.run

        def f() -> requests.Response:
            while True:
                try:
                    return original_run()
                except Exception as e:
                    print(f'\033[31m{e}\033[0m')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            pass
                        case 'B':
                            sys.exit(0)

        self.run = f
        return self

    def handle_status_code(self) -> 'Request':
        original_run = self.run

        def f() -> requests.Response:
            while True:
                if (response := original_run()).status_code == 200:
                    return response
                else:
                    print(f'请求失败 (state: {response.status_code})')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            pass
                        case 'B':
                            sys.exit(0)

        self.run = f
        return self


def input_choice(choices: dict[str, str | None], extra_prompt: str = ''):
    prompt = ('\033[95;1m>\033[0m ' + extra_prompt
              + ', '.join([f'\033[96;1m[{key}]\033[0m {value}' for key, value in choices.items() if value is not None])
              + '? ')
    while (inp := input(prompt).upper()) not in choices: pass
    return inp


def write_song_files(response_obj: dict, media_file: mutagen.FileType,
                     lyrics_file_path: str | os.PathLike[str]) -> FileDataDict:
    media_file['title'] = [response_obj['defaultName']]
    media_file['artist'] = [i['name'] for i in response_obj['artists']]
    if 'artist_separator' in CONFIG:
        media_file['artist'] = [CONFIG['artist_separator'].join(media_file['artist'])]
    if response_obj['albums']:
        media_file['album'] = [i['name'] for i in response_obj['albums']]
        if 'album_separator' in CONFIG:
            media_file['album'] = [CONFIG['album_separator'].join(media_file['album'])]
    else:
        media_file.pop('album', None)
    media_file['date'] = [response_obj['publishDate']]
    media_file['comment'] = [f'Vocadb ID: {response_obj['id']}, song type: {response_obj['songType']}']
    if 'minMilliBpm' in response_obj:
        media_file['bpm'] = [round((response_obj['minMilliBpm'] + response_obj['maxMilliBpm']) * .0005)]
    else:
        media_file.pop('bpm', None)
    if response_obj['lyrics']: open(lyrics_file_path, 'w', encoding='utf-8').write(response_obj['lyrics'][0]['value'])
    return {
        'id': response_obj['id'],
        'time': DateString.dump(datetime.datetime.now())
    }


if os.path.isfile('config.json'):
    CONFIG: Configure = json.load(open('config.json', 'r', encoding='utf-8'))
else:
    CONFIG: Configure = {
        'sort': 'None',
        'maxResults': 10,
        'search_length_offset': 5
    }
    json.dump(CONFIG, open('config.json', 'w', encoding='utf-8'), ensure_ascii=False)
if os.path.isfile('data.json'):
    data: dict[str, dict[str, FileDataDict]] = json.load(open('data.json', 'r', encoding='utf-8'))
else:
    data: dict[str, dict[str, FileDataDict]] = {}
try:
    DIR_PATH = str(Args.args.path.resolve())
    DIR_FILE_LIST = os.listdir(DIR_PATH)
    if DIR_PATH not in data: data[DIR_PATH] = {}
    # 检查数据库所有歌曲
    for db_file in list(data[DIR_PATH].keys()):
        if db_file not in DIR_FILE_LIST:
            print(f'数据库中的文件 {db_file} 已被移动或删除。')
            match input_choice({'D': '删除', 'M': '将数据绑定到新文件', 'J': '跳过', 'B': '终止'}):
                case 'D':
                    del data[DIR_PATH][db_file]
                case 'M':
                    while True:
                        inp = input('\033[95m>\033[0m 新文件名? ')
                        if inp not in DIR_FILE_LIST:
                            print(f'文件 {inp} 不存在。')
                        elif pathlib.Path(inp).suffix not in AUDIO_EXTENSIONS:
                            print(f'{inp} 不是支持的音频文件。')
                        else:
                            break
                    data[DIR_PATH][inp] = data[DIR_PATH][db_file]
                    del data[DIR_PATH][db_file]
                case 'J':
                    continue
                case 'B':
                    sys.exit(0)
    # 检查文件夹的所有文件
    for file_index, file_name in enumerate(DIR_FILE_LIST):
        file_full_path = pathlib.Path(DIR_PATH) / file_name
        # 剔除非音频文件
        if not os.path.isfile(file_full_path) or file_full_path.suffix.lower() not in AUDIO_EXTENSIONS: continue
        try:
            media: mutagen.FileType | None = mutagen.File(file_full_path, easy=True)
            if media is None: continue
        except mutagen.MutagenError:
            continue
        state = 0
        if Args.args.command == 'import' and file_name not in data[DIR_PATH]:
            print(f'{file_index + 1:{len(str(len(DIR_FILE_LIST)))}d}\033[90m/\033[36m{len(DIR_FILE_LIST)}'
                  f' \033[1;93m{file_name}\033[0m')
            print(f'  \033[36m[时长]   \033[97m{int(media.info.length) // 60}'
                  f'\033[90m:\033[97m{round(media.info.length % 60, 2)}\033[0m')
            if 'title' in media: print(f'  \033[36m[标题]   \033[1;97m{media['title'][0]}\033[0m')
            if 'artist' in media: print(
                f'  \033[36m[艺术家] \033[97m{'\033[0m, \033[97m'.join(media['artist'])}\033[0m')
            if 'album' in media: print(f'  \033[36m[专辑]   \033[97m{'\033[0m, \033[97m'.join(media['album'])}\033[0m')
            query = media['artist'][0] if 'artist' in media else file_full_path.stem
            search_results = []
            song_id: int = -1
            while state != -1:
                match state:
                    case 0:
                        params = {
                            'query': query,
                            'sort': CONFIG['sort'],
                            'maxResults': CONFIG['maxResults']
                        }
                        if 'search_length_offset' in CONFIG:
                            params |= {
                                'minLength': max(0, round(media.info.length - CONFIG['search_length_offset'])),
                                'maxLength': min(0x7fffffff,
                                                 round(media.info.length + CONFIG['search_length_offset']))
                            }
                        search_results = Request('https://vocadb.net/api/songs',
                                                 params).handle_error().handle_status_code().run().json()['items']
                        if len(search_results) == 1:
                            song_id = search_results[0]['id']
                            state = 1
                            continue
                        if len(search_results) == 0:
                            print('\033[33m无结果\033[0m')
                        num_length = len(str(len(search_results))) + 2
                        for ind, song in enumerate(search_results):
                            print(f'\033[1;93m{ind + 1}.'.ljust(num_length, ' ') +
                                  f'\033[0;97m{song['defaultName']} \033[90m{song['artistString']}\n'
                                  f'\033[36m{' ' * num_length}[歌曲类型]\033[0m '
                                  f'{'\033[96m' if song['songType'] == 'Original' else ''}'
                                  f'{song['songType']} '
                                  f'\033[36m[链接] \033[4;94mhttps://vocadb.net/S/{song['id']}\033[0m')
                        match inp := (input_choice({'S': '搜索关键词', 'I': '指定 VocaDB ID', 'J': '跳过', 'B': '终止'}
                                                   | {str(i): None for i in range(1, len(search_results) + 1)},
                                                   '输入\033[1;93m编号\033[0m选择候选项, ' if search_results else '')):
                            case 'S':
                                query = input('\033[95m>\033[0m 关键词? ')
                            case 'I':
                                song_id = -1
                                while song_id <= 0:
                                    try:
                                        song_id = int(input('\033[95m>\033[0m ID? '))
                                    except ValueError:
                                        pass
                                state = 1
                            case 'J':
                                state = -1
                            case 'B':
                                sys.exit(0)
                            case _:
                                song_id = search_results[int(inp) - 1]['id']
                                state = 1
                    case 1:
                        while True:
                            response = Request(f'https://vocadb.net/api/songs/{song_id}', params={
                                'fields': 'Albums, Artists, Lyrics, Bpm'
                            }).handle_error().run()
                            if response.status_code == 200:
                                break
                            print(f'请求失败 (state: {response.status_code})')
                            match input_choice({'R': '重试', 'I': '指定 VocaDB ID', 'B': '终止'}):
                                case 'R':
                                    pass
                                case 'I':
                                    song_id = -1
                                    while song_id <= 0:
                                        try:
                                            song_id = int(input('\033[95m>\033[0m ID? '))
                                        except ValueError:
                                            pass
                                case 'B':
                                    sys.exit(0)
                        song_data = response.json()
                        print(f'\033[0;97m{song_data['defaultName']} \033[90m{song_data['artistString']}\033[0m\n'
                              f'  \033[36m[歌曲类型]\033[0m'
                              f' {'\033[96m' if song_data['songType'] == 'Original' else ''}'
                              f'{song_data['songType']} '
                              f'\033[36m[时长] \033[97m{song_data['lengthSeconds'] // 60}'
                              f'\033[90m:\033[97m{song_data['lengthSeconds'] % 60} '
                              + ('\033[36m[BPM] \033[97m' +
                                 (str(song_data['minMilliBpm'] // 1000)
                                  if song_data['minMilliBpm'] == song_data['maxMilliBpm'] else
                                  f'{song_data['minMilliBpm'] // 1000}'
                                  f'\033[90m~\033[97m{song_data['maxMilliBpm'] // 1000}')
                                 + ' ' if 'minMilliBpm' in song_data else '') +
                              f'\033[36m[链接] \033[4;94mhttps://vocadb.net/S/{song_data['id']}\033[0m')
                        if song_data['albums']:
                            print('  \033[36m[专辑] \033[97m' +
                                  '\033[90m, \033[97m'.join(i['name'] for i in song_data['albums']) + '\033[0m')
                        if song_data['lyrics']:
                            print('  \033[36m[歌词]')
                            for i in song_data['lyrics']:
                                if not i['value']: continue
                                print(f'    \033[1m[{', '.join(i['cultureCodes'])}]\033[0m '
                                      f'{i['value'].replace('\r\n', '\n').split('\n')[0]}'
                                      f'{'\033[90m...\033[0m' if '\n' in i['value'] else ''}')
                        match input_choice(
                            {'A': '\033[1;94m应用\033[0m', 'S': '重新搜索', 'I': '指定 VocaDB ID',
                             'J': '跳过', 'B': '终止'}
                        ):
                            case 'A':
                                data[DIR_PATH][file_name] = write_song_files(song_data, media,
                                                                             file_full_path.with_suffix('.lrc'))
                                media.save()
                                json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
                                state = -1
                            case 'S':
                                query = input('\033[95m>\033[0m 关键词? ')
                                state = 0
                            case 'I':
                                song_id = -1
                                while song_id <= 0:
                                    try:
                                        song_id = int(input('\033[95m>\033[0m ID? '))
                                    except ValueError:
                                        pass
                            case 'J':
                                state = -1
                            case 'B':
                                sys.exit(0)
        elif Args.args.command == 'check' and file_name in data[DIR_PATH]:
            song_id: int = data[DIR_PATH][file_name]['id']
            last_update_time = DateString.load(data[DIR_PATH][file_name]['time'])
            if last_update_time > Args.args.time:
                continue
            print(f'{file_index + 1:{len(str(len(DIR_FILE_LIST)))}d}\033[90m/\033[36m{len(DIR_FILE_LIST)}'
                  f' \033[0m正在检查 \033[93m{file_name}\033[0m')
            while True:
                response = Request(f'https://vocadb.net/api/songs/{song_id}/versions').handle_error().run()
                if response.status_code == 200:
                    break
                print(f'请求失败 (state: {response.status_code})')
                match input_choice({'R': '重试', 'I': '指定 VocaDB ID', 'B': '终止'}):
                    case 'R':
                        pass
                    case 'I':
                        song_id = -1
                        while song_id <= 0:
                            try:
                                song_id = int(input('\033[95m>\033[0m ID? '))
                            except ValueError:
                                pass
                    case 'B':
                        sys.exit(0)
            if all(DateString.load(version['created']) < last_update_time
                   for version in response.json()['archivedVersions']):
                print('- 无更改')
                data[DIR_PATH][file_name]['time'] = DateString.dump(datetime.datetime.now())
                json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
                continue
            print('- \033[1m有更改\033[0m')
            response = Request(f'https://vocadb.net/api/songs/{song_id}',
                               {'fields': 'Albums, Artists, Lyrics, Bpm'}
                               ).handle_error().handle_status_code().run()
            if os.path.isfile(file_full_path.with_suffix('.lrc')):
                os.remove(file_full_path.with_suffix('.lrc'))
            data[DIR_PATH][file_name] = write_song_files(response.json(), media,
                                                         file_full_path.with_suffix('.lrc'))
            media.save()
            json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
finally:
    json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
