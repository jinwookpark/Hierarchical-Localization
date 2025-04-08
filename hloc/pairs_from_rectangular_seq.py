import argparse
import collections.abc as collections
from pathlib import Path
from typing import List, Optional, Union

from hloc import logger
from hloc.utils.io import list_h5_names
from hloc.utils.parsers import parse_image_lists

def main(
    output: Path,
    image_list: Optional[Union[Path, List[str]]] = None,
    features: Optional[Path] = None,
    circle_size: Optional[int] = 10,
    step_size: Optional[int] = 4,
    radius_size: Optional[int] = 2,
    flag_over_range: Optional[bool] = True,
) -> None:
    """
    Generate pairs of images based on sequential matching and optional loop closure.
    Args:
        output (Path): The output file path where the pairs will be saved.
        image_list (Optional[Union[Path, List[str]]]):
            A path to a file containing a list of images or a list of image names.
        features (Optional[Path]):
            A path to a feature file containing image features.
    Raises:
        ValueError: If neither image_list nor features are provided,
            or if image_list is of an unknown type.
    Returns:
        None
    """
    if image_list is not None:
        if isinstance(image_list, (str, Path)):
            print(image_list)
            names_q = parse_image_lists(image_list)
        elif isinstance(image_list, collections.Iterable):
            names_q = list(image_list)
        else:
            raise ValueError(f"Unknown type for image list: {image_list}")
    elif features is not None:
        names_q = list_h5_names(features)
    else:
        raise ValueError("Provide either a list of images or a feature file.")

    pairs = []
    N = len(names_q)

    for i in range(N - 1):
        frame1 = names_q[i]
        pre, num, circle_num, ext = split_frame_000000_00_jpg(frame1) # frame 000000 00 jpg
        f1 = int(num)
        circle_list=get_sudo_fisheye_pair(int(circle_num), r=radius_size, size=circle_size, flag_over_range=flag_over_range)
        for f2 in range(f1,f1+step_size):
            frame2_pre=f"{pre}_{f2:06d}_"
            for c2 in circle_list:
                frame2=f"{frame2_pre}{c2:02d}.{ext}"
                if frame2 in names_q:
                    if frame1 == frame2:
                        continue
                    pairs.append([frame1,frame2])
    pairs =  get_unique_pairs(pairs)

    logger.info(f"Found {len(pairs)} pairs.")
    with open(output, "w") as f:
        f.write("\n".join(" ".join([i, j]) for i, j in pairs))

def split_frame_000000_00_jpg(x):
    # EX) filename = "frame_000000_00.jpg"
    # first, second, num, ext
    # frame  000000   00  jpg
    base, ext = x.rsplit('.', 1)
    prefix, num = base.rsplit('_', 1)
    first, second = prefix.split('_', 1)
    return first, second, num, ext

def get_unique_pairs(data):
    unique = []
    seen = set()
    for pair in data:
        # 순서에 상관없이 같은 쌍으로 보기 위해 정렬한 튜플을 생성합니다.
        key = tuple(sorted(pair))
        if key not in seen:
            seen.add(key)
            unique.append(pair)
    return unique

def get_sudo_fisheye_pair(x=0, r=2, size=8, flag_over_range=True):
    tmp=list(range(-r, r + 1))
    y = [i + x for i in tmp]
    out=[]
    for n in y:
        if flag_over_range:
            if n<0:
                n=size+n
            elif n>=size:
                n=n-size
            out.append(n)
        else:
            if 0<=n and n<size:
                out.append(n)
    return out
def format_number(n: int) -> str:
    return f"{n:02d}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Create a list of image pairs basedon the sequence of images on alphabetic order
        """
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--image_list", type=Path)
    parser.add_argument("--features", type=Path)
    parser.add_argument("--circle_size", type=int, default=10)
    parser.add_argument("--step_size", type=int, default=4)
    parser.add_argument("--radius_size", type=int, default=2)
    args = parser.parse_args()
    main(**args.__dict__)
