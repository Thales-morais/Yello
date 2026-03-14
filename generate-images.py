#!/usr/bin/env python3
"""
Yello Brand Image Generator — Powered by Gemini Imagen
=======================================================
Gera todos os assets de imagem do design system Yello usando a API do Gemini.

Uso:
    python3 generate-images.py --key YOUR_GEMINI_API_KEY

Os arquivos serão salvos em ./assets/generated/
O brand-guide.html será atualizado para referenciar as imagens geradas.

Modelo: gemini-2.0-flash-preview-image-generation (nano-banana)
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Image Prompts — cada template do design system
# ---------------------------------------------------------------------------

BRAND_ASSETS = [
    # ── Social Media ────────────────────────────────────────────────────────
    {
        "id": "social_instagram_post",
        "filename": "social-instagram-post.png",
        "size": "1024x1024",
        "category": "social",
        "label": "Instagram Post",
        "prompt": (
            "Professional brand marketing image for 'Yello', a Brazilian operational intelligence company. "
            "Square format (1:1). Vibrant yellow background (#F5C518). "
            "Bold black text 'Inteligência que transforma.' in large sans-serif. "
            "Abstract chameleon silhouette in bottom right, minimal geometric style. "
            "Bottom left: small Yello wordmark logo. "
            "Clean, modern, Apple-inspired aesthetic. High contrast. "
            "No gradients, flat bold design, premium feel."
        ),
    },
    {
        "id": "social_instagram_story",
        "filename": "social-instagram-story.png",
        "size": "1024x1820",
        "category": "social",
        "label": "Instagram Story",
        "prompt": (
            "Vertical brand story for 'Yello' operational intelligence company. "
            "Portrait 9:16 format. Dark background #0A0A0A. "
            "Large yellow 'Y' letterform as hero element, geometric and bold. "
            "Subtext: 'Operações que funcionam.' in white DM Sans font. "
            "Small chameleon icon near bottom. "
            "Minimal, high-end, luxury tech aesthetic."
        ),
    },
    {
        "id": "social_linkedin_banner",
        "filename": "social-linkedin-banner.png",
        "size": "1584x396",
        "category": "social",
        "label": "LinkedIn Banner",
        "prompt": (
            "Professional LinkedIn company banner for 'Yello' — operational intelligence company. "
            "Wide format 4:1. Dark charcoal background #1C1C1E. "
            "Left side: 'Yello' wordmark in bold yellow Syne-style font. "
            "Center: tagline 'Inteligência Operacional' in clean white. "
            "Right: abstract data visualization lines in yellow, suggesting intelligence/analytics. "
            "Corporate but distinctive, premium tech company aesthetic."
        ),
    },
    {
        "id": "social_twitter_card",
        "filename": "social-twitter-card.png",
        "size": "1200x628",
        "category": "social",
        "label": "Twitter/X Card",
        "prompt": (
            "Twitter/X social share card for Yello brand. "
            "16:9 format. Off-white background #F5F5F7. "
            "Bold yellow horizontal bar at top (20px). "
            "Large text: 'Sua operação, inteligente.' Syne font style, dark #0A0A0A. "
            "Bottom: Yello logo + website yello.ai. "
            "Minimal, clean, tech startup aesthetic."
        ),
    },
    # ── Presentation Slides ─────────────────────────────────────────────────
    {
        "id": "slide_title",
        "filename": "slide-title.png",
        "size": "1920x1080",
        "category": "slides",
        "label": "Slide: Capa",
        "prompt": (
            "Presentation title slide for Yello operational intelligence company. "
            "16:9 widescreen. Full black background #0A0A0A. "
            "Center: 'yello' wordmark in massive yellow Syne-style font (300px). "
            "Below: 'Inteligência Operacional' in small white DM Sans. "
            "Subtle yellow dot grid pattern in background, very subtle. "
            "Bottom right: chameleon mascot silhouette in yellow. "
            "Dramatic, high-contrast, Apple Keynote quality."
        ),
    },
    {
        "id": "slide_content",
        "filename": "slide-content.png",
        "size": "1920x1080",
        "category": "slides",
        "label": "Slide: Conteúdo",
        "prompt": (
            "Content presentation slide template for Yello company. "
            "16:9 widescreen. Clean white background #F5F5F7. "
            "Top left: small Yello yellow logo mark. "
            "Left side: thick yellow vertical bar (8px). "
            "Main heading 'Resultados que importam' in bold dark #0A0A0A Syne font. "
            "Three content blocks below with bullet points. "
            "Bottom: thin yellow line. "
            "Professional, clean, data-forward design."
        ),
    },
    {
        "id": "slide_metrics",
        "filename": "slide-metrics.png",
        "size": "1920x1080",
        "category": "slides",
        "label": "Slide: Métricas",
        "prompt": (
            "Data/metrics slide for Yello operational intelligence company. "
            "16:9 widescreen. Dark #1C1C1E background. "
            "Three large metric cards: '47%', '3x', '98%' in huge yellow Syne font. "
            "Below each: description in small white text. "
            "Background: subtle data grid lines in dark gray. "
            "Modern, impactful, financial-grade data visualization aesthetic."
        ),
    },
    # ── Logo Variations ─────────────────────────────────────────────────────
    {
        "id": "logo_on_yellow",
        "filename": "logo-on-yellow.png",
        "size": "800x400",
        "category": "logos",
        "label": "Logo s/ fundo amarelo",
        "prompt": (
            "Yello company logo on yellow background. "
            "Yellow background #F5C518. "
            "Dark black 'yello' wordmark text in bold Syne-style font, centered. "
            "Small chameleon icon to the left of the text. "
            "Clean, high contrast, brand identity application."
        ),
    },
    {
        "id": "logo_on_dark",
        "filename": "logo-on-dark.png",
        "size": "800x400",
        "category": "logos",
        "label": "Logo s/ fundo escuro",
        "prompt": (
            "Yello company logo on dark background. "
            "Dark background #0A0A0A. "
            "Yellow 'yello' wordmark text in bold Syne-style font, centered. "
            "Small yellow chameleon icon to the left. "
            "White negative space. High contrast brand identity."
        ),
    },
    {
        "id": "logo_on_white",
        "filename": "logo-on-white.png",
        "size": "800x400",
        "category": "logos",
        "label": "Logo s/ fundo branco",
        "prompt": (
            "Yello company logo on white background. "
            "Pure white background #FFFFFF. "
            "Black 'yello' wordmark in bold Syne-style font, centered. "
            "Yellow chameleon icon to the left. "
            "Clean, minimal brand mark, print-ready quality."
        ),
    },
    {
        "id": "app_icon",
        "filename": "logo-app-icon.png",
        "size": "1024x1024",
        "category": "logos",
        "label": "App Icon (1024px)",
        "prompt": (
            "Mobile app icon for Yello company. Square 1:1. "
            "Rounded square shape with yellow background #F5C518. "
            "Bold black letter 'Y' in center, geometric and strong. "
            "Very small chameleon tail curving around the Y. "
            "iOS/Android app icon style, premium, simple, recognizable at small sizes."
        ),
    },
    {
        "id": "favicon",
        "filename": "logo-favicon.png",
        "size": "64x64",
        "category": "logos",
        "label": "Favicon (64px)",
        "prompt": (
            "Minimal favicon for Yello company. Tiny 64x64px. "
            "Yellow square background. Bold black 'Y' letterform. "
            "Extremely simple, readable at 16x16 pixel size. No details."
        ),
    },
    # ── Brand Cards ─────────────────────────────────────────────────────────
    {
        "id": "business_card_front",
        "filename": "card-business-front.png",
        "size": "1020x638",
        "category": "cards",
        "label": "Cartão de Visita — Frente",
        "prompt": (
            "Business card front design for Yello company. "
            "Standard business card proportions 85x54mm (landscape). "
            "Dark background #0A0A0A. "
            "Left: yellow 'yello' wordmark + chameleon icon stacked. "
            "Right: person name 'Ana Costa' in white Syne font, "
            "title 'Head de Produto' in yellow DM Sans, "
            "email 'ana@yello.ai' and phone in gray. "
            "Bottom: thin yellow accent line. "
            "Premium, luxury business card, dark edition."
        ),
    },
    {
        "id": "business_card_back",
        "filename": "card-business-back.png",
        "size": "1020x638",
        "category": "cards",
        "label": "Cartão de Visita — Verso",
        "prompt": (
            "Business card back design for Yello company. "
            "Standard business card proportions (landscape). "
            "Full yellow background #F5C518. "
            "Center: large chameleon mascot illustration in dark #0A0A0A, minimal linework style. "
            "Bottom: 'yello.ai' URL in small dark text. "
            "Bold, memorable, brand-forward back of business card."
        ),
    },
    {
        "id": "email_signature",
        "filename": "card-email-signature.png",
        "size": "600x200",
        "category": "cards",
        "label": "Assinatura de E-mail",
        "prompt": (
            "Email signature design for Yello company. "
            "Wide horizontal format 600x200px. White background. "
            "Left: vertical yellow line separator, then Yello logo (icon + wordmark small). "
            "Right of separator: Name 'Ana Costa' bold dark, "
            "title in gray, email and LinkedIn links in yellow. "
            "Bottom: very thin yellow line across full width. "
            "Clean, professional, corporate email signature."
        ),
    },
    # ── Marketing Banners ───────────────────────────────────────────────────
    {
        "id": "banner_web",
        "filename": "banner-web-hero.png",
        "size": "1440x600",
        "category": "banners",
        "label": "Banner Web Hero",
        "prompt": (
            "Hero banner for Yello company website. "
            "1440x600px. Dark background #0A0A0A. "
            "Left side: massive 'Inteligência\nOperacional.' text in white Syne font (split 2 lines). "
            "Yellow highlight on 'Inteligência'. "
            "Right side: abstract 3D chameleon illustration in yellow and dark tones. "
            "CTA button 'Conheça a Yello' in yellow. "
            "Premium, tech company, startup hero section."
        ),
    },
    {
        "id": "banner_ebook",
        "filename": "banner-ebook-cover.png",
        "size": "800x1130",
        "category": "banners",
        "label": "Capa de E-book",
        "prompt": (
            "E-book cover design for Yello company. "
            "Portrait A4 proportions. Dark navy background. "
            "Bold yellow geometric shapes as decorative elements (triangles, lines). "
            "Title: 'O Guia Definitivo de\nInteligência Operacional' in white Syne font. "
            "Subtitle: 'Como escalar operações sem perder controle' in yellow. "
            "Bottom: Yello logo in white + year 2025. "
            "Professional, editorial, high-end ebook cover."
        ),
    },
]


# ---------------------------------------------------------------------------
# Gemini API Client
# ---------------------------------------------------------------------------

def generate_image(prompt: str, api_key: str, model: str = "gemini-2.0-flash-preview-image-generation") -> bytes | None:
    """Call Gemini image generation API and return PNG bytes."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"  HTTP {exc.code}: {error_body[:300]}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"  Error: {exc}", file=sys.stderr)
        return None

    # Extract base64 image from response
    try:
        candidates = body.get("candidates", [])
        for candidate in candidates:
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    b64 = part["inlineData"]["data"]
                    return base64.b64decode(b64)
    except Exception as exc:
        print(f"  Parse error: {exc}", file=sys.stderr)

    print(f"  No image in response: {json.dumps(body)[:300]}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Yello Brand Image Generator via Gemini")
    parser.add_argument("--key", "-k", required=True, help="Gemini API key")
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-2.0-flash-preview-image-generation",
        help="Gemini model for image generation (default: gemini-2.0-flash-preview-image-generation)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="assets/generated",
        help="Output directory (default: assets/generated)",
    )
    parser.add_argument(
        "--category",
        "-c",
        choices=["social", "slides", "logos", "cards", "banners", "all"],
        default="all",
        help="Which category of assets to generate",
    )
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=2.0,
        help="Delay between API calls in seconds (default: 2.0)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    assets = BRAND_ASSETS
    if args.category != "all":
        assets = [a for a in BRAND_ASSETS if a["category"] == args.category]

    print(f"\n🦎 Yello Brand Image Generator")
    print(f"   Model  : {args.model}")
    print(f"   Output : {output_dir.resolve()}")
    print(f"   Assets : {len(assets)} images to generate")
    print(f"   {'─' * 50}\n")

    success = 0
    failed = 0

    for i, asset in enumerate(assets, 1):
        filepath = output_dir / asset["filename"]
        print(f"[{i:02d}/{len(assets):02d}] {asset['label']}")
        print(f"        → {filepath}")

        if filepath.exists():
            print(f"        ✓ Already exists, skipping.\n")
            success += 1
            continue

        print(f"        ⏳ Generating...")
        img_bytes = generate_image(asset["prompt"], args.key, args.model)

        if img_bytes:
            filepath.write_bytes(img_bytes)
            size_kb = len(img_bytes) // 1024
            print(f"        ✅ Saved ({size_kb} KB)\n")
            success += 1
        else:
            print(f"        ❌ Failed to generate\n")
            failed += 1

        if i < len(assets):
            time.sleep(args.delay)

    print(f"{'─' * 50}")
    print(f"✅ Success : {success}")
    print(f"❌ Failed  : {failed}")
    print(f"\nNext step: open brand-guide.html in your browser.")
    print(f"The guide automatically loads images from {output_dir}/\n")


if __name__ == "__main__":
    main()
