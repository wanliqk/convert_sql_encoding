from pathlib import Path
from charset_normalizer import from_bytes
import argparse
import shutil


# 需要被转换的中文编码
TARGET_ENCODINGS = {
    "gb2312",
    "gbk",
    "gb18030",
}


def detect_encoding(file_path: Path) -> str | None:
    """
    检测文件编码
    """
    raw_data = file_path.read_bytes()

    # 空文件不处理
    if not raw_data:
        return None

    result = from_bytes(raw_data).best()

    if result is None:
        return None

    return result.encoding.lower() if result.encoding else None


def convert_to_utf8(file_path: Path, source_encoding: str, backup: bool = True) -> None:
    """
    将指定编码的文件转换为 UTF-8
    """
    raw_data = file_path.read_bytes()

    # 使用检测到的编码读取
    text = raw_data.decode(source_encoding, errors="strict")

    # 备份原文件
    if backup:
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy2(file_path, backup_path)

    # 以 UTF-8 写回
    file_path.write_text(text, encoding="utf-8", newline="")


def main():
    parser = argparse.ArgumentParser(
        description="检测当前目录下所有 SQL 文件编码，并将 GB2312/GBK/GB18030 转换为 UTF-8"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只检测，不执行转换"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="转换前不备份原文件"
    )

    args = parser.parse_args()

    current_dir = Path.cwd()
    sql_files = list(current_dir.rglob("*.sql"))

    if not sql_files:
        print("当前目录下没有找到 .sql 文件")
        return

    print(f"共找到 {len(sql_files)} 个 SQL 文件\n")

    converted_count = 0
    skipped_count = 0
    failed_count = 0

    for file_path in sql_files:
        try:
            encoding = detect_encoding(file_path)

            if encoding is None:
                print(f"[跳过] {file_path}：无法检测编码或为空文件")
                skipped_count += 1
                continue

            print(f"[检测] {file_path}：{encoding}")

            if encoding in TARGET_ENCODINGS:
                if args.dry_run:
                    print(f"  -> 将会转换为 UTF-8")
                else:
                    convert_to_utf8(
                        file_path,
                        source_encoding=encoding,
                        backup=not args.no_backup
                    )
                    print(f"  -> 已转换为 UTF-8")

                converted_count += 1
            else:
                skipped_count += 1

        except UnicodeDecodeError:
            print(f"[失败] {file_path}：使用 {encoding} 解码失败")
            failed_count += 1

        except Exception as e:
            print(f"[失败] {file_path}：{e}")
            failed_count += 1

    print("\n处理完成")
    print(f"转换文件数：{converted_count}")
    print(f"跳过文件数：{skipped_count}")
    print(f"失败文件数：{failed_count}")


if __name__ == "__main__":
    main()