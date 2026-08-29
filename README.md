# ynotl VocaDB Song Searcher

> 一个轻量级命令行工具，用于将本地音频文件与 [VocaDB](https://vocadb.net) 上的歌曲信息同步，支持写入元数据并记录更新状态。

## 功能特性

- **导入模式**：自动读取文件夹中的音频文件，根据文件标签或文件名搜索 VocaDB，交互式选择匹配歌曲，并将以下信息写入音频文件：
    - 标题
    - 艺术家
    - 专辑
    - 发布日期
    - BPM（如果有）
    - 备注
    - 歌词（保存为同名`.lrc`文件）
- **检查更新模式**：比对本地缓存与 VocaDB 的版本历史，若歌曲信息有更新，则重新下载最新元数据和歌词。
- **持久化数据库**：使用`data.json`记录每个文件对应的 VocaDB ID 和最后更新时间，避免重复处理。
- **交互式选择**：当搜索到多个结果时，提供编号选择、重新搜索或手动指定 ID 的选项。
- **可配置参数**：通过`config.json`调整搜索排序、结果数量和时间容差。

## 使用方法

### 命令格式

```bash
python ynotl import <path>
python ynotl check <path> [time]
```

### 参数说明

- `import <path>`  
  遍历`<path>`下的所有 `.m4a` 文件，若尚未导入则进行搜索和写入。
- `check <path> [time]`  
  检查`<path>`下已导入的、最后更新时间早于`time`的（若指定）文件在 VocaDB 中是否有更新，若有则刷新元数据。  
  其中`time`格式为`YYYY-MM-DD`

### 首次运行

1. 将`ynotl.py`放在任意目录，确保已安装依赖（见下文）。
2. 运行命令，程序会自动生成`config.json`和`data.json`。
3. 根据交互提示操作即可。

## 依赖安装

```bash
pip install requests mutagen
```

## 配置文件说明

`config.json`会在首次运行时自动生成，字段如下：

- `sort`（字符串，默认值`"None"`）  
  可用值`None`, `Name`, `AdditionDate`, `PublishDate`, `FavoritedTimes`, `RatingScore`, `TagUsageCount`, `SongType`，
指定按照关键词搜索结果的排列顺序（见 [VocaDB API 的 api/songs](https://vocadb.net/swagger/index.html)）

- `maxResults`（正整数，默认值`10`）  
  指定按照关键词搜索返回的结果数量（见 [VocaDB API 的 api/songs](https://vocadb.net/swagger/index.html)）

- `search_length_offset`（正整数或不指定，默认值`5`）  
  若指定，搜索时增加时长限制歌曲文件时长±`search_length_offset`秒

- `artist_separator`（字符串或不指定，默认不指定）  
  若指定，写入歌曲文件的艺术家时使用以此值分隔的单个字符串而不是多值

- `album_separator`（字符串或不指定，默认不指定）  
  若指定，写入歌曲文件的专辑时使用以此值分隔的单个字符串而不是多值

- `lyrics_lang`（字符串或不指定，默认不指定）  
  若不指定，保存歌词时选择歌曲原语言；若指定，尽可能选择此值指定的语言

## 示例

```bash
# 导入 ~/Music/Vocaloid 下的所有 .m4a 文件
python ynotl.py import ~/Music/Vocaloid

# 检查该文件夹下所有已导入文件的更新
python ynotl.py check ~/Music/Vocaloid

# 只检查上次更新时间在 2026-01-01 前的文件
python ynotl.py check ~/Music/Vocaloid 2026-01-01
```

## 许可证

本项目基于 **MIT License** 开源，详情请见 [LICENSE](LICENSE) 文件。
