#!/usr/bin/env python3
import os
import json
import argparse

from novel_to_anime import NovelToAnimeConverter


def main():
    parser = argparse.ArgumentParser(description='将小说转换为动漫视频')
    parser.add_argument('novel', help='小说文本文件路径')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    parser.add_argument('-n', '--name', default='anime.mp4', help='输出视频文件名')
    parser.add_argument('-c', '--config', help='配置文件路径 (JSON格式)')
    
    args = parser.parse_args()
    
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    converter = NovelToAnimeConverter(config)
    
    try:
        result = converter.convert(args.novel, args.output, args.name)
        print(f"\n🎉 转换成功! 视频已保存到: {result}")
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        exit(1)


if __name__ == "__main__":
    main()
