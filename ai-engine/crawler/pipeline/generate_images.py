"""
게시글 이미지 생성 스크립트 (SDXL via Replicate)
=================================================
posts/ 폴더의 게시글 데이터를 읽어 각 게시글에 상품 이미지를 생성한다.

실행:
  python -m crawler.pipeline.generate_images --input ./crawler/data/posts --output ./crawler/data/images

옵션:
  --category 디지털기기     특정 카테고리만 처리
  --limit 10               카테고리당 최대 N건만 처리 (테스트용)
  --delay 1.0              API 호출 간 딜레이 (초)
  --resume                 이미 생성된 이미지는 건너뛰기 (중단 후 재시작용)

사전 준비:
  1. pip install replicate
  2. .env에 REPLICATE_API_TOKEN 추가
"""

import argparse
import json
import os
import re
import time
import random
import hashlib
import requests
from pathlib import Path

from dotenv import load_dotenv

try:
    import replicate
except ImportError:
    print("ERROR: pip install replicate")
    exit(1)

# .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR.parent / ".env"
load_dotenv(ENV_PATH)

# Replicate API 토큰 확인
if not os.getenv("REPLICATE_API_TOKEN"):
    print("ERROR: .env에 REPLICATE_API_TOKEN을 설정하세요.")
    print("  https://replicate.com/account/api-tokens 에서 발급")
    exit(1)

# SDXL 모델
SDXL_MODEL = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"

# ── 카테고리별 촬영 환경 힌트 ──
CATEGORY_PHOTO_STYLE = {
    "디지털기기": "on a white desk, natural lighting, slightly angled top-down view",
    "가전제품": "in a living room setting, natural daylight, eye-level shot",
    "패션잡화": "on a clean white surface, soft studio lighting, flat lay",
    "남성의류": "hanging on a wooden hanger against white wall, natural light",
    "여성의류": "flat lay on white bedsheet, overhead shot, soft natural light",
    "스포츠/레저": "on grass or gym floor, natural outdoor lighting",
    "출산/유아동": "in a bright nursery room, warm soft lighting",
    "취미/게임": "on a desk next to a monitor, ambient room lighting",
    "뷰티/미용": "on a marble surface, bright studio lighting, close-up",
    "반려동물용품": "on a clean floor, natural indoor lighting",
    "생활용품": "in a tidy room, natural daylight from window",
    "가구/인테리어": "in a modern room, natural daylight, wide angle",
    "도서": "stacked on a wooden desk, warm reading lamp light",
    "식품": "on a kitchen counter, bright overhead lighting",
    "티켓/교환권": "on a white desk, flat lay, overhead shot, clean background",
    "기타 중고물품": "on a neutral surface, natural indoor lighting",
}

# ── 촬영 앵글 풀 (다양성) ──
PHOTO_ANGLES = [
    "slightly angled top-down view",
    "straight-on eye-level view",
    "45-degree angle view",
    "overhead flat lay",
    "slight low angle looking up",
]

# ── 사용감 표현 ──
CONDITION_HINTS = {
    "S급": "brand new, pristine condition, no visible wear",
    "A급": "excellent condition, minimal signs of use, very clean",
    "B급": "good condition, some minor signs of use, light scratches",
    "C급": "fair condition, visible wear and scratches, still functional",
    "부품용": "worn condition, visible damage, for parts only",
}


def build_image_prompt(post: dict, image_index: int = 0) -> str:
    """게시글 정보로 이미지 생성 프롬프트 구성"""
    category = post.get("category", "기타 중고물품")
    condition = post.get("condition", "A급")
    sensitive = post.get("sensitiveAttributes", {})

    # 상품 설명 구성
    product_parts = []
    brand = sensitive.get("브랜드", "")
    model = sensitive.get("모델명", "")
    kind = sensitive.get("종류", "")
    color = sensitive.get("색상", "")

    if brand:
        product_parts.append(brand)
    if model:
        product_parts.append(model)
    if kind:
        product_parts.append(kind)

    product_name = " ".join(product_parts) if product_parts else post.get("title", "used item")
    color_hint = f", {color} color" if color else ""

    # 카테고리별 환경
    photo_style = CATEGORY_PHOTO_STYLE.get(category, "on a neutral surface, natural lighting")

    # 상태 힌트
    condition_hint = CONDITION_HINTS.get(condition, "used condition")

    # 앵글 다양성
    angle = random.choice(PHOTO_ANGLES)

    # 두 번째 사진은 다른 앵글
    if image_index == 1:
        alt_angles = [a for a in PHOTO_ANGLES if a != angle]
        angle = random.choice(alt_angles)
        photo_style = photo_style.replace("top-down", "close-up detail")

    prompt = (
        f"A realistic smartphone photo of a second-hand {product_name}{color_hint}, "
        f"{condition_hint}, {photo_style}, {angle}, "
        f"casual amateur photography style, realistic lighting, "
        f"no text, no watermark, no logo overlay, "
        f"looks like a real marketplace listing photo taken by a regular person"
    )

    return prompt


def generate_image(prompt: str, max_retries: int = 3) -> str | None:
    """SDXL로 이미지 생성, URL 반환"""
    for attempt in range(max_retries):
        try:
            output = replicate.run(
                SDXL_MODEL,
                input={
                    "prompt": prompt,
                    "negative_prompt": (
                        "text, watermark, logo, banner, collage, "
                        "multiple items, blurry, low quality, "
                        "cartoon, illustration, 3d render, "
                        "professional studio, commercial photography"
                    ),
                    "width": 1024,
                    "height": 1024,
                    "num_outputs": 1,
                    "scheduler": "K_EULER",
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                    "refine": "expert_ensemble_refiner",
                    "high_noise_frac": 0.8,
                },
            )

            if output and len(output) > 0:
                return str(output[0])

        except Exception as e:
            print(f" [오류] attempt {attempt + 1}: {e}")
            time.sleep(3)

    return None


def download_image(url: str, save_path: Path) -> bool:
    """URL에서 이미지 다운로드"""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f" [다운로드 오류] {e}")
    return False


def process_posts(input_dir: Path, output_dir: Path, image_dir: Path,
                  category_filter: str = None, limit: int = None,
                  delay: float = 1.0, resume: bool = False):
    """게시글 데이터를 읽어 이미지 생성 + images 필드 업데이트"""

    post_files = sorted(input_dir.glob("posts_*.jsonl"))
    if not post_files:
        print(f"ERROR: {input_dir}에 posts_*.jsonl 파일이 없습니다.")
        return

    total_generated = 0
    total_skipped = 0

    for pf in post_files:
        # 카테고리 필터
        cat_name = pf.stem.replace("posts_", "")
        if category_filter and category_filter not in cat_name:
            continue

        print(f"\n{'=' * 50}")
        print(f"[{cat_name}]")
        print(f"{'=' * 50}")

        posts = []
        with open(pf, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    posts.append(json.loads(line))

        if limit:
            posts = posts[:limit]

        cat_image_dir = image_dir / cat_name
        cat_image_dir.mkdir(parents=True, exist_ok=True)

        updated_posts = []

        for i, post in enumerate(posts):
            post_id = post.get("_id", f"unknown_{i}")
            image_count = post.get("imageCount", 1)
            images = []

            print(f"  [{i + 1}/{len(posts)}] {post.get('title', '')[:40]}...", end="", flush=True)

            for img_idx in range(image_count):
                img_filename = f"{post_id}_{img_idx}.png"
                img_path = cat_image_dir / img_filename
                relative_path = f"images/{cat_name}/{img_filename}"

                # resume 모드: 이미 있으면 건너뛰기
                if resume and img_path.exists():
                    images.append(relative_path)
                    total_skipped += 1
                    continue

                # 프롬프트 생성 + 이미지 생성
                prompt = build_image_prompt(post, img_idx)
                url = generate_image(prompt)

                if url:
                    if download_image(url, img_path):
                        images.append(relative_path)
                        total_generated += 1
                    else:
                        print(f" (다운로드 실패)", end="")
                else:
                    print(f" (생성 실패)", end="")

                time.sleep(delay)

            post["images"] = images
            updated_posts.append(post)
            print(f" → {len(images)}장")

        # 업데이트된 게시글 저장
        out_path = output_dir / pf.name
        with open(out_path, "w", encoding="utf-8") as f:
            for post in updated_posts:
                f.write(json.dumps(post, ensure_ascii=False) + "\n")

        print(f"  저장: {out_path} ({len(updated_posts)}건)")

    # 통합 파일 재생성
    all_output = output_dir / "posts_all.jsonl"
    with open(all_output, "w", encoding="utf-8") as fall:
        for pf in sorted(output_dir.glob("posts_*.jsonl")):
            if pf.name == "posts_all.jsonl":
                continue
            with open(pf, "r", encoding="utf-8") as fin:
                for line in fin:
                    fall.write(line)

    print(f"\n{'=' * 50}")
    print(f"이미지 생성 완료")
    print(f"  생성: {total_generated}장")
    print(f"  건너뜀 (resume): {total_skipped}장")
    print(f"  이미지 저장: {image_dir}")
    print(f"  게시글 업데이트: {output_dir}")
    print(f"  예상 비용: ~${total_generated * 0.003:.2f} (SDXL)")


def main():
    parser = argparse.ArgumentParser(description="게시글 이미지 생성 (SDXL via Replicate)")
    parser.add_argument("--input", type=str, required=True, help="posts/ 디렉토리 (변환된 게시글)")
    parser.add_argument("--output", type=str, default=None, help="출력 디렉토리 (기본: input과 동일)")
    parser.add_argument("--image-dir", type=str, default=None, help="이미지 저장 디렉토리 (기본: output/images)")
    parser.add_argument("--category", type=str, default=None, help="특정 카테고리만 처리")
    parser.add_argument("--limit", type=int, default=None, help="카테고리당 최대 N건 (테스트용)")
    parser.add_argument("--delay", type=float, default=1.0, help="API 호출 간 딜레이 초 (기본 1.0)")
    parser.add_argument("--resume", action="store_true", help="이미 생성된 이미지 건너뛰기")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output) if args.output else input_dir
    image_dir = Path(args.image_dir) if args.image_dir else output_dir / "images"

    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("게시글 이미지 생성 (SDXL via Replicate)")
    print(f"입력: {input_dir}")
    print(f"이미지 저장: {image_dir}")
    if args.category:
        print(f"카테고리 필터: {args.category}")
    if args.limit:
        print(f"카테고리당 제한: {args.limit}건")
    print("=" * 60)

    process_posts(
        input_dir=input_dir,
        output_dir=output_dir,
        image_dir=image_dir,
        category_filter=args.category,
        limit=args.limit,
        delay=args.delay,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()