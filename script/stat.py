import re
import os
import pandas as pd
import click
import time
from typing import List, Tuple


def load(filename: str) -> Tuple[str, str]:
    with open(filename, 'r') as fp:
        content = fp.read()

    title = re.search(r"^title: (.+)$", content, re.MULTILINE)[1]
    opening = content.find('---')
    closing = content.find('---', opening + 1)
    content = content[closing + len('---'):]
    content = content.strip()
    return title, content

def load_all(dir: str, exclude: List[str]) -> List[str]:
    paths = os.walk(dir, followlinks=False)
    files = []
    for path in paths:
        for filename in path[2]:
            files.append(os.path.join(path[0], filename))

    # only hard links
    files = [file for file in files if not os.path.islink(file)]

    # filter exclude
    files = [file for file in files if file not in exclude]

    # filter only markdown
    files = [file for file in files if os.path.splitext(file)[-1].lower() == '.md']
    return [*map(load, files)]

@click.command()
@click.argument('dir', type=click.Path(exists=True, resolve_path=True, file_okay=False))
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
def main(dir: str, exclude: List[str], output_plot: str) -> None:
    contents = load_all(dir, exclude)
    now = time.strftime("%Y-%m-%d")
    print(f"> Statistics of {now}")
    print(f"> Total {len(contents)} posts")
    df = pd.DataFrame(data=contents, columns=['title', 'content'])
    df['words'] = df.apply(lambda row: len(row['content']), axis=1)
    print("> Stats of posts")
    print(df.describe())
    print(f"> Median: {df['words'].median()}")
    post_max = df[df['words'] == df['words'].max()].iloc[0]['title']
    post_min = df[df['words'] == df['words'].min()].iloc[0]['title']
    print(f"> Lognest post: {post_max}")
    print(f"> Shortest post: {post_min}")

    if output_plot:
        fig_name = os.path.join(output_plot, f'hist-{now}.svg')
        fig = df.plot.hist(bins=100)
        fig.figure.savefig(fig_name)
        print(f"> Saved figure in {fig_name}")

if __name__ == '__main__':
    main()
