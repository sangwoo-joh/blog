import re
import os
import pandas as pd
import click
import time
from typing import List, Tuple

HERE = os.path.dirname(__file__)

def load_content(filepath: str) -> Tuple[str, str]:
    with open(filepath, 'r') as fp:
        content = fp.read()

    title = re.search(r"^title: (.+)$", content, re.MULTILINE)[1]
    opening = content.find('---')
    closing = content.find('---', opening + 1)
    content = content[closing + len('---'):]
    content = content.strip()
    return title, content

def load_post_paths(dir: str, exclude: List[str]) -> List[str]:
    paths = os.walk(dir, followlinks=False)
    files = []
    for path in paths:
        for filename in path[2]:
            files.append(os.path.join(path[0], filename))

    def filtering(file: str) -> bool:
        return (not os.path.islink(file) and  # only hard links
                file not in exclude and  # filter excludes
                os.path.splitext(file)[-1].lower() == '.md')  # markdown

    return [file for file in files if filtering(file)]

@click.command()
@click.option(
    '--year', '-y',
    default=time.strftime("%Y"),
    help="Filter by year. Default is the current year. Set \"all\" if you want to see statistic for all posts.",
)
@click.option(
    '--exclude', '-e',
    type=click.Path(exists=True, resolve_path=True, dir_okay=False),
    multiple=True,
    help="File to exclude from statistics",
)
@click.option(
    '--output-plot', '-o',
    type=click.Path(exists=True, resolve_path=True, file_okay=False),
    help="Directory to write histogram plot. Figure file name will be hist-{now}.svg.",
)
def main(year: str, exclude: List[str], output_plot: str) -> None:
    print(f"> Statistics of {year}")

    post_dir = os.path.join(os.path.dirname(HERE), "_posts")
    post_paths = load_post_paths(post_dir, exclude)
    if year != 'all':
        post_paths = [p for p in post_paths if os.path.basename(p)[:4] == year]
    contents = [*map(load_content, post_paths)]

    df = pd.DataFrame(data=contents, columns=['title', 'content'])
    df['characters'] = df.apply(lambda row: len(row['content']), axis=1)
    post_max = df[df['characters'] == df['characters'].max()].iloc[0]['title']
    post_min = df[df['characters'] == df['characters'].min()].iloc[0]['title']

    print(f"> Total {len(contents)} posts")
    print("> Stats of posts")
    print(df.describe())
    print(f"> Median: {df['characters'].median()}")
    print(f"> Longest post: {post_max}")
    print(f"> Shortest post: {post_min}")

    if output_plot:
        fig_name = os.path.join(output_plot, f'hist-{year}.svg')
        fig = df.plot.hist(bins=100)
        fig.figure.savefig(fig_name)
        print(f"> Saved figure in {fig_name}")

if __name__ == '__main__':
    main()
