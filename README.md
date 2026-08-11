# ynotl VocaDB Song Searcher

> 一个轻量级命令行工具，用于将本地音频文件（`.m4a`）与 [VocaDB](https://vocadb.net) 上的歌曲信息同步，支持写入元数据并记录更新状态。

## ✨ 功能特性

- **导入模式**：自动读取文件夹中的 `.m4a` 文件，根据文件标签或文件名搜索 VocaDB，交互式选择匹配歌曲，并将以下信息写入音频文件：
  - 标题（`©nam`）
  - 艺术家（`©ART`）
  - 专辑（`©alb`）
  - 发布日期（`©day`）
  - BPM（`tmpo`）
  - 备注（`©cmt`，包含 VocaDB ID 和歌曲类型）
  - 歌词（保存为同名 `.lrc` 文件）
- **检查更新模式**：比对本地缓存与 VocaDB 的版本历史，若歌曲信息有更新，则重新下载最新元数据和歌词。
- **持久化数据库**：使用 `data.json` 记录每个文件对应的 VocaDB ID 和最后更新时间，避免重复处理。
- **交互式选择**：当搜索到多个结果时，提供编号选择、重新搜索或手动指定 ID 的选项。
- **可配置参数**：通过 `config.json` 调整搜索排序、结果数量和时间容差。

## 🚀 使用方法

### 命令格式

```bash
python ynotl.py import <目录路径>
python ynotl.py check <目录路径> {all | <YYYY-MM-DD>}
```

### 参数说明

- `import <path>`  
  遍历 `<path>` 下的所有 `.m4a` 文件，若尚未导入则进行搜索和写入。
- `check <path> {all | <YYYY-MM-DD>}`  
  检查 `<path>` 下已导入的文件，若 VocaDB 中有更新（晚于指定日期或全部检查），则刷新元数据。

### 首次运行

1. 将 `ynotl.py` 放在任意目录，确保已安装依赖（见下文）。
2. 运行命令，程序会自动生成 `config.json` 和 `data.json`。
3. 根据交互提示操作即可。

## 📦 依赖安装

```bash
pip install requests mutagen
```

## ⚙️ 配置文件说明

`config.json` 在首次运行时自动生成，包含以下字段：

```json
{
  "sort": "None",
  "maxResults": 10,
  "search_length_offset": 5
}
```

## ⚠️ 注意事项

- 当前仅支持 `.m4a` 文件
- 歌词会保存为与音频文件同目录、同名的 `.lrc` 文件。

## 🧩 示例

```bash
# 导入 ~/Music/Vocaloid 下的所有 .m4a 文件
python ynotl.py import ~/Music/Vocaloid

# 检查该文件夹下所有已导入文件的更新
python ynotl.py check ~/Music/Vocaloid all

# 只检查 2025-01-01 之后有更新的文件
python ynotl.py check ~/Music/Vocaloid 2026-01-01
```

## 📄 许可证

本项目基于 **MIT License** 开源，详情请见 [LICENSE](LICENSE) 文件。