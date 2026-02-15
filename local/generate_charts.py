#!/usr/bin/env python3
"""選挙区ごとの積み上げ棒グラフ画像を生成するスクリプト"""

import gzip
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.font_manager import FontProperties
import numpy as np

# 日本語フォント設定（環境に合わせて変更）
JP_FONTS = [
    'UD Digi Kyokasho N',
    'BIZ UDGothic',
    'Hiragino Sans', 'Hiragino Kaku Gothic ProN',
    'Noto Sans JP', 'Noto Sans CJK JP',
    'Yu Gothic', 'MS Gothic', 'IPAGothic',
]
for fn in JP_FONTS:
    if any(fn.lower() in f.name.lower() for f in fm.fontManager.ttflist):
        plt.rcParams['font.family'] = fn
        break

YEARS = ['2021', '2024', '2026']
FILES = {
    '2021': '../hr2021_districts.csv.gz',
    '2024': '../hr2024_districts.csv.gz',
    '2026': '../hr2026_districts.csv.gz',
}

PARTY_COLORS = {
    '自民': '#c8383d',
    '立憲': '#1b4e8e',
    '中道': '#1b4e8e',
    '維新': '#38b44a',
    '公明': '#8050b0',
    '共産': '#e87777',
    '国民': '#f5c100',
    'れいわ': '#ed6d9e',
    '社民': '#24b89b',
    '参政': '#f08300',
    'Ｎ党': '#cccc00',
    '無所': '#999999',
    '諸派': '#bbbbbb',
    '減ゆ': '#7b68ee',
    '保守': '#8b4513',
    'みらい': '#00bfff',
}

CODE_TO_PREF = {
    1:'北海道',2:'青森',3:'岩手',4:'宮城',5:'秋田',6:'山形',7:'福島',
    8:'茨城',9:'栃木',10:'群馬',11:'埼玉',12:'千葉',13:'東京',14:'神奈川',
    15:'新潟',16:'富山',17:'石川',18:'福井',19:'山梨',20:'長野',21:'岐阜',22:'静岡',23:'愛知',
    24:'三重',25:'滋賀',26:'京都',27:'大阪',28:'兵庫',29:'奈良',30:'和歌山',
    31:'鳥取',32:'島根',33:'岡山',34:'広島',35:'山口',
    36:'徳島',37:'香川',38:'愛媛',39:'高知',
    40:'福岡',41:'佐賀',42:'長崎',43:'熊本',44:'大分',45:'宮崎',46:'鹿児島',47:'沖縄',
}
PREF_TO_CODE = {v: k for k, v in CODE_TO_PREF.items()}


def text_color_for(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return '#ffffff' if lum <= 0.55 else '#222222'


def load_data():
    all_data = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for y in YEARS:
        path = os.path.join(script_dir, FILES[y])
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        for row in rows:
            if row['party'] == 'れい':
                row['party'] = 'れいわ'
        all_data[y] = rows
    return all_data


def get_districts(all_data):
    """都道府県ごとに選挙区を収集"""
    pref_districts = defaultdict(set)
    for y in YEARS:
        for row in all_data[y]:
            pref_districts[row['prefecture']].add(row['district'])

    result = {}
    for pref, dists in pref_districts.items():
        def sort_key(d):
            import re
            m = re.search(r'(\d+)区', d)
            return int(m.group(1)) if m else 0
        result[pref] = sorted(dists, key=sort_key)
    return result


def render_chart(all_data, district, output_path):
    year_data = {}
    for y in YEARS:
        cands = [r for r in all_data[y] if r['district'] == district]
        cands.sort(key=lambda r: int(r['votes']), reverse=True)
        year_data[y] = cands

    max_cands = max(len(year_data[y]) for y in YEARS)
    if max_cands == 0:
        return

    fig, ax = plt.subplots(figsize=(8.53, 6.4))

    x = np.arange(len(YEARS))
    bar_width = 0.55
    bottoms = np.zeros(len(YEARS))

    for i in range(max_cands):
        values = []
        colors = []
        labels_info = []
        for y in YEARS:
            if i < len(year_data[y]):
                c = year_data[y][i]
                v = int(c['votes'])
                values.append(v)
                colors.append(PARTY_COLORS.get(c['party'], '#aaaaaa'))
                labels_info.append(c)
            else:
                values.append(0)
                colors.append('none')
                labels_info.append(None)

        bars = ax.bar(x, values, bar_width, bottom=bottoms, color=colors, edgecolor='white', linewidth=0.3)

        # ラベル描画
        for j, (bar, cand) in enumerate(zip(bars, labels_info)):
            if cand is None or int(cand['votes']) == 0:
                continue
            bar_height = bar.get_height()
            if bar_height < 20000:
                continue
            cx = bar.get_x() + bar.get_width() / 2
            cy = bar.get_y() + bar_height / 2

            name = cand['name'].replace(' ', '').replace('\u3000', '')
            pct = round(float(cand['vshare']))
            party = cand['party']
            win = ''
            if cand['win_smd'] == '1':
                win = '\n当選'
            elif cand['win_pr'] == '1':
                win = '\n復活'

            label = f"{name}\n{party} {pct}%{win}"
            tc = text_color_for(PARTY_COLORS.get(cand['party'], '#aaaaaa'))
            if pct <= 20:
                fontsize = 14
            else:
                fontsize = 16
            fp = FontProperties(family='UD Digi Kyokasho N', weight='bold', size=fontsize)

            ax.text(cx, cy, label, ha='center', va='center',
                    fontproperties=fp, color=tc,
                    linespacing=1.2)

        bottoms += np.array(values)

    ax.set_xticks(x)
    ax.set_xticklabels(YEARS, fontsize=15)
    ax.set_ylim(0, 300000)
    ax.yaxis.set_major_locator(plt.MultipleLocator(100000))
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f'{int(v/10000)}万' if v >= 10000 else f'{int(v):,}')
    )
    ax.tick_params(axis='y', labelsize=15)
    ax.set_title(district, fontsize=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_data = load_data()
    pref_districts = get_districts(all_data)

    count = 0
    total = sum(len(d) for d in pref_districts.values())

    for pref, districts in sorted(pref_districts.items(), key=lambda x: PREF_TO_CODE.get(x[0], 99)):
        code = PREF_TO_CODE.get(pref, 0)
        for dist in districts:
            count += 1
            filename = f"{code:02d}{dist}.jpg"
            output_path = os.path.join(script_dir, filename)
            print(f"[{count}/{total}] {filename}")
            render_chart(all_data, dist, output_path)

    print(f"\n完了: {count}枚の画像を生成しました")


if __name__ == '__main__':
    main()
