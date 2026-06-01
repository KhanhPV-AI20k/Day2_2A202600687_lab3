from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "agent_workflow.png"

WIDTH = 1900
HEIGHT = 1800
BG = "#f7f8fb"
INK = "#172033"
MUTED = "#5d667a"
BLUE = "#dceafe"
BLUE_BORDER = "#5b8def"
GREEN = "#dff3e6"
GREEN_BORDER = "#3f9c61"
ORANGE = "#fff0d5"
ORANGE_BORDER = "#d5912d"
RED = "#ffe1df"
RED_BORDER = "#d65b50"
PURPLE = "#eadffc"
PURPLE_BORDER = "#8664d5"
GRAY = "#eef1f6"
GRAY_BORDER = "#9aa4b6"


def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


TITLE = load_font(42, bold=True)
SUBTITLE = load_font(22)
HEAD = load_font(24, bold=True)
BODY = load_font(19)
SMALL = load_font(16)


def wrapped(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def box(draw, xy, title, body, fill, outline):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=3)
    draw.text((x1 + 24, y1 + 20), title, font=HEAD, fill=INK)
    y = y1 + 66
    for line in wrapped(draw, body, BODY, x2 - x1 - 48):
        draw.text((x1 + 24, y), line, font=BODY, fill=MUTED)
        y += 26


def diamond(draw, center, size, title, body, fill, outline):
    cx, cy = center
    w, h = size
    points = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
    draw.polygon(points, fill=fill, outline=outline)
    draw.line(points + [points[0]], fill=outline, width=3)
    title_box = draw.textbbox((0, 0), title, font=HEAD)
    draw.text((cx - (title_box[2] - title_box[0]) / 2, cy - 34), title, font=HEAD, fill=INK)
    body_box = draw.textbbox((0, 0), body, font=BODY)
    draw.text((cx - (body_box[2] - body_box[0]) / 2, cy + 2), body, font=BODY, fill=MUTED)


def arrow(draw, start, end, label=None, bend=None):
    if bend:
        points = [start, bend, end]
        draw.line(points, fill=INK, width=3, joint="curve")
    else:
        draw.line([start, end], fill=INK, width=3)

    x1, y1 = start if not bend else bend
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    tip = end
    left = (x2 - ux * 18 + px * 8, y2 - uy * 18 + py * 8)
    right = (x2 - ux * 18 - px * 8, y2 - uy * 18 - py * 8)
    draw.polygon([tip, left, right], fill=INK)

    if label:
        mid_x = (start[0] + end[0]) / 2 if not bend else (bend[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2 if not bend else (bend[1] + end[1]) / 2
        bounds = draw.textbbox((0, 0), label, font=SMALL)
        pad = 8
        draw.rounded_rectangle(
            (mid_x - (bounds[2] - bounds[0]) / 2 - pad, mid_y - 14, mid_x + (bounds[2] - bounds[0]) / 2 + pad, mid_y + 12),
            radius=8,
            fill=BG,
        )
        draw.text((mid_x - (bounds[2] - bounds[0]) / 2, mid_y - 10), label, font=SMALL, fill=INK)


def main():
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    draw.text((70, 50), "Ecommerce ReAct Agent Workflow", font=TITLE, fill=INK)
    draw.text(
        (70, 108),
        "Generated from run_agent.py, src/agent/agent.py, src/core/*_provider.py, src/tools/*, and src/telemetry/*.",
        font=SUBTITLE,
        fill=MUTED,
    )

    left = 120
    center = 690
    right = 1260
    w = 460
    h = 170

    box(
        draw,
        (left, 190, left + w, 190 + h),
        "1. Entry point",
        "run_agent.py loads .env, creates OpenAIProvider, imports TOOLS, builds ReActAgent(max_steps=5), then calls agent.run(question).",
        BLUE,
        BLUE_BORDER,
    )
    box(
        draw,
        (center, 190, center + w, 190 + h),
        "2. Agent start",
        "ReActAgent.run(user_input) logs AGENT_START and sets current_prompt to the user's question.",
        GREEN,
        GREEN_BORDER,
    )
    box(
        draw,
        (center, 440, center + w, 440 + h),
        "3. System prompt",
        "get_system_prompt() lists available tools and enforces Thought, Action, Observation, Final Answer format.",
        GRAY,
        GRAY_BORDER,
    )
    box(
        draw,
        (center, 690, center + w, 690 + h),
        "4. LLM call",
        "llm.generate(current_prompt, system_prompt) calls the selected provider. run_agent.py uses OpenAIProvider by default.",
        PURPLE,
        PURPLE_BORDER,
    )
    diamond(
        draw,
        (center + w // 2, 1035),
        (500, 220),
        "5. Parse response",
        "Action or Final Answer?",
        ORANGE,
        ORANGE_BORDER,
    )
    box(
        draw,
        (right, 710, right + w, 710 + h),
        "Action path",
        "_parse_action() extracts tool_name(args). _execute_tool() finds the matching tool dictionary entry and calls its function.",
        ORANGE,
        ORANGE_BORDER,
    )
    box(
        draw,
        (right, 970, right + w, 970 + h),
        "Tool functions",
        "calculator evaluates math. search_web, browse_url, and extract_product_info use Tavily for search/extraction and product evidence.",
        BLUE,
        BLUE_BORDER,
    )
    box(
        draw,
        (right, 1230, right + w, 1230 + h),
        "Observation loop",
        "Tool output is appended as Observation to current_prompt. The loop repeats until a final answer or max_steps.",
        GREEN,
        GREEN_BORDER,
    )
    box(
        draw,
        (left, 930, left + w, 930 + h),
        "Final answer path",
        "_parse_final_answer() extracts text after 'Final Answer:'. AGENT_END is logged, then the answer is returned.",
        GREEN,
        GREEN_BORDER,
    )
    box(
        draw,
        (left, 1230, left + w, 1230 + h),
        "Fallbacks",
        "If no Action or Final Answer is parsed, return parse error. If max_steps is reached, return max-steps message.",
        RED,
        RED_BORDER,
    )
    box(
        draw,
        (right, 190, right + w, 190 + h),
        "Telemetry",
        "src/telemetry/logger.py writes AGENT_START and AGENT_END JSON events to console and logs/YYYY-MM-DD.log.",
        GRAY,
        GRAY_BORDER,
    )

    arrow(draw, (left + w, 275), (center, 275))
    arrow(draw, (center + w, 275), (right, 275), "log start/end")
    arrow(draw, (center + w // 2, 360), (center + w // 2, 440))
    arrow(draw, (center + w // 2, 610), (center + w // 2, 690))
    arrow(draw, (center + w // 2, 860), (center + w // 2, 925))
    arrow(draw, (center + w + 15, 1035), (right, 795), "Action")
    arrow(draw, (right + w // 2, 880), (right + w // 2, 970))
    arrow(draw, (right + w // 2, 1140), (right + w // 2, 1230))
    arrow(draw, (right, 1315), (center + w, 775), "repeat", bend=(1210, 1315))
    arrow(draw, (center, 1035), (left + w, 1015), "Final Answer")
    arrow(draw, (center + 70, 1125), (left + w, 1315), "unparsed")

    legend = [
        ("Entry/config", BLUE, BLUE_BORDER),
        ("Agent state", GREEN, GREEN_BORDER),
        ("LLM/provider", PURPLE, PURPLE_BORDER),
        ("Decision/tool", ORANGE, ORANGE_BORDER),
        ("Fallback", RED, RED_BORDER),
        ("Telemetry/context", GRAY, GRAY_BORDER),
    ]
    x = 90
    y = 1710
    for label, fill, border in legend:
        draw.rounded_rectangle((x, y, x + 26, y + 26), radius=6, fill=fill, outline=border, width=2)
        draw.text((x + 36, y + 2), label, font=SMALL, fill=MUTED)
        x += 260

    image.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
