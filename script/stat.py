import re
import os
import pandas as pd
import click
import time
from typing import List, Tuple

HERE = os.path.dirname(__file__)

def load_content(filename: str) -> Tuple[str, str]:
    with open(filename, 'r') as fp:
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
def main(exclude: List[str], output_plot: str) -> None:
    post_dir = os.path.join(os.path.dirname(HERE), "_posts")
    this_year = time.strftime("%Y")
    print(f"> Statistics of {this_year}")

    post_paths = load_post_paths(post_dir, exclude)
    contents = [*map(load_content, post_paths)]
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
        fig_name = os.path.join(output_plot, f'hist-{this_year}.svg')
        fig = df.plot.hist(bins=100)
        fig.figure.savefig(fig_name)
        print(f"> Saved figure in {fig_name}")

if __name__ == '__main__':
    main()
