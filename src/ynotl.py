import datetime
import json
import os
import pathlib
import requests
import sys
from mutagen.mp4 import MP4
from typing import TypedDict

if argv_syntax_pass := sys.argv[1] == 'import':
    if argv_syntax_pass := len(sys.argv) == 3:
        if not (argv_syntax_pass := os.path.isdir(sys.argv[2])):
            print('目录不存在')
elif argv_syntax_pass := sys.argv[1] == 'check':
    if argv_syntax_pass := len(sys.argv) == 4:
        if argv_syntax_pass := os.path.isdir(sys.argv[2]):
            if not (argv_syntax_pass := sys.argv[3] == 'all'):
                try:
                    datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d')
                    argv_syntax_pass = True
                except:
                    print('日期不合法')
                    argv_syntax_pass = False
        else:
            print('目录不存在')
if not argv_syntax_pass:
    print('usage:\n'
          '  import <path>\n'
          '  check <path> {all | <YYYY-MM-DD>}')
    sys.exit(1)
# 常数
# AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.mp4', '.ape', '.wv', '.aiff', '.aif'}
AUDIO_EXTENSIONS = {'.m4a'}  # WIP（
HEADERS = {'User-Agent': 'ynotl.py/1.0 (contact: 3365139905@qq.com)'}
DEFAULT_CONFIG = {
    "sort": "None",
    "maxResults": 10,
    "search_length_offset": 5
}


class FileDataDict(TypedDict):
    id: int
    time: str


class DateString:
    @staticmethod
    def load(date_string: str) -> datetime.datetime:
        if '.' in date_string: return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f')
        return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def dump(datetime_obj: datetime.datetime) -> str:
        return datetime_obj.strftime('%Y-%m-%dT%H:%M:%S.%f')


def input_choice(choices: dict[str, str | None], extra_prompt: str = ''):
    prompt = ('\033[95;1m>\033[0m ' + extra_prompt
              + ', '.join([f'\033[96;1m[{key}]\033[0m {value}' for key, value in choices.items() if value is not None])
              + '? ')
    while (inp := input(prompt).upper()) not in choices: pass
    return inp


def write_song_files(response_obj: dict, media_file: MP4, lyrics_file_path: str | os.PathLike[str]) -> FileDataDict:
    media_file['©nam'] = [response_obj['defaultName']]
    media_file['©ART'] = [i['name'] for i in response_obj['artists']]
    if response_obj['albums']:
        media_file['©alb'] = [i['name'] for i in response_obj['albums']]
    elif '©alb' in media_file:
        del media_file['©alb']
    media_file['©day'] = [response_obj['publishDate']]
    media_file['©cmt'] = [f'Vocadb ID: {response_obj['id']}, song type: {response_obj['songType']}']
    if 'minMilliBpm' in response_obj:
        media_file['tmpo'] = [round((response_obj['minMilliBpm'] + response_obj['maxMilliBpm']) * .0005)]
    else:
        media_file['tmpo'] = []
    if response_obj['lyrics']: open(lyrics_file_path, 'w', encoding='utf-8').write(response_obj['lyrics'][0]['value'])
    return {
        'id': response_obj['id'],
        'time': DateString.dump(datetime.datetime.now())
    }


if os.path.isfile('config.json'):
    CONFIG = json.load(open('config.json', 'r', encoding='utf-8'))
else:
    CONFIG = DEFAULT_CONFIG
    json.dump(DEFAULT_CONFIG, open('config.json', 'w', encoding='utf-8'), ensure_ascii=False)
if os.path.isfile('data.json'):
    data: dict[str, dict[str, FileDataDict]] = json.load(
        open('data.json', 'r', encoding='utf-8'))
else:
    data: dict[str, dict[str, FileDataDict]] = {}
try:
    DIR_PATH = str(pathlib.Path(sys.argv[2]).resolve())
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
        state = 0
        if sys.argv[1] == 'import' and file_name not in data[DIR_PATH]:
            print(f'{file_index + 1:{len(str(len(DIR_FILE_LIST)))}d}\033[90m/\033[36m{len(DIR_FILE_LIST)}'
                  f' \033[1;93m{file_name}\033[0m')
            media = MP4(file_full_path)
            print(f'  \033[36m[时长]   \033[97m{int(media.info.length) // 60}'
                  f'\033[90m:\033[97m{round(media.info.length % 60, 2)}\033[0m')
            if '©nam' in media: print(f'  \033[36m[标题]   \033[1;97m{media['©nam'][0]}\033[0m')
            if '©ART' in media: print(f'  \033[36m[艺术家] \033[97m{'\033[0m, \033[97m'.join(media['©ART'])}\033[0m')
            if '©alb' in media: print(f'  \033[36m[专辑]   \033[97m{'\033[0m, \033[97m'.join(media['©alb'])}\033[0m')
            query = media['©nam'][0] if '©nam' in media else file_full_path.stem
            search_results = []
            song_id: int = -1
            while state != -1:
                match state:
                    case 0:
                        try:
                            response = requests.get('https://vocadb.net/api/songs', params={
                                'query': query,
                                'minLength': max(0, round(media.info.length - CONFIG['search_length_offset'])),
                                'maxLength': min(0x7fffffff, round(media.info.length + CONFIG['search_length_offset'])),
                                'sort': CONFIG['sort'],
                                'maxResults': CONFIG['maxResults']
                            }, headers=HEADERS, timeout=10)
                        except Exception as e:
                            print(f'发生错误: {e}')
                            match input_choice({'R': '重试', 'B': '终止'}):
                                case 'R':
                                    continue
                                case 'B':
                                    sys.exit(0)
                        if response.status_code == 200:
                            search_results = response.json()['items']
                            if len(search_results) == 1:
                                song_id = search_results[0]['id']
                                state = 1
                            else:
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
                                match inp := (
                                    input_choice({'S': '搜索关键词', 'I': '指定 VocaDB ID', 'J': '跳过', 'B': '终止'}
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
                        else:
                            print(f'请求失败 (state: {response.status_code})')
                            match input_choice({'R': '重试', 'B': '终止'}):
                                case 'R':
                                    continue
                                case 'B':
                                    sys.exit(0)
                    case 1:
                        try:
                            response = requests.get(f'https://vocadb.net/api/songs/{song_id}', params={
                                'fields': 'Albums, Artists, Lyrics, Bpm'
                            }, headers=HEADERS, timeout=10)
                        except Exception as e:
                            print(f'\033[31m{e}\033[0m')
                            match input_choice({'R': '重试', 'B': '终止'}):
                                case 'R':
                                    continue
                                case 'B':
                                    sys.exit(0)
                        if response.status_code == 200:
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
                        else:
                            print(f'请求 https://vocadb.net/api/songs/{song_id} 失败 (state: {response.status_code})')
                            match input_choice({'R': '重试', 'B': '终止'}):
                                case 'R':
                                    continue
                                case 'B':
                                    sys.exit(0)
        elif sys.argv[1] == 'check' and file_name in data[DIR_PATH]:
            song_id: int = data[DIR_PATH][file_name]['id']
            last_update_time = DateString.load(data[DIR_PATH][file_name]['time'])
            if sys.argv[3] != 'all' and last_update_time > datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d'):
                continue
            print(f'{file_index + 1:{len(str(len(DIR_FILE_LIST)))}d}\033[90m/\033[36m{len(DIR_FILE_LIST)}'
                  f' \033[0m正在检查 \033[93m{file_name}\033[0m')
            while True:
                try:
                    response = requests.get(f'https://vocadb.net/api/songs/{song_id}/versions', params={},
                                            headers=HEADERS, timeout=10)
                except Exception as e:
                    print(f'发生错误: {e}')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            continue
                        case 'B':
                            sys.exit(0)
                if response.status_code == 200:
                    break
                else:
                    print(f'请求失败 (state: {response.status_code})')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            continue
                        case 'B':
                            sys.exit(0)
            if all(DateString.load(version['created']) < last_update_time
                   for version in response.json()['archivedVersions']):
                print('- 无更改')
                data[DIR_PATH][file_name]['time'] = DateString.dump(datetime.datetime.now())
                json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
                continue
            print('- \033[1m有更改\033[0m')
            if os.path.isfile(file_full_path.with_suffix('.lrc')):
                os.remove(file_full_path.with_suffix('.lrc'))
            while True:
                try:
                    response = requests.get(f'https://vocadb.net/api/songs/{song_id}', params={
                        'fields': 'Albums, Artists, Lyrics, Bpm'
                    }, headers=HEADERS, timeout=10)
                except Exception as e:
                    print(f'\033[31m{e}\033[0m')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            continue
                        case 'B':
                            sys.exit(0)
                if response.status_code == 200:
                    media = MP4(file_full_path)
                    data[DIR_PATH][file_name] = write_song_files(response.json(), media,
                                                                 file_full_path.with_suffix('.lrc'))
                    media.save()
                    json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
                    break
                else:
                    print(f'请求 https://vocadb.net/api/songs/{song_id} 失败 (state: {response.status_code})')
                    match input_choice({'R': '重试', 'B': '终止'}):
                        case 'R':
                            continue
                        case 'B':
                            sys.exit(0)
finally:
    json.dump(data, open('data.json', 'w', encoding='utf-8'), ensure_ascii=False)
