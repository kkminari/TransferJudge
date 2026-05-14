#!/usr/bin/env python3
"""TransferJudge 프레임워크 다이어그램 + Cold-Start 개념도 생성"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm
import os

# macOS 한글 폰트 설정
for fname in ['AppleGothic', 'Apple SD Gothic Neo', 'NanumGothic']:
    fonts = fm.findSystemFonts()
    matched = [f for f in fonts if fname.replace(' ', '') in f.replace(' ', '')]
    if matched:
        plt.rcParams['font.family'] = fname
        break
plt.rcParams['axes.unicode_minus'] = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "..", "diagrams")

# ──────────────────────────────────────────────
# 1. 전체 프레임워크 다이어그램
# ──────────────────────────────────────────────
def draw_framework():
    fig, ax = plt.subplots(1, 1, figsize=(15, 8.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Colors
    C_INPUT = '#DBEAFE'
    C_PROFILER = '#D1FAE5'
    C_JUDGE = '#EDE9FE'
    C_GATE = '#F3E8FF'
    C_OUTPUT = '#FEE2E2'
    C_EVAL = '#FEF3C7'
    C_TRANSFER = '#059669'
    C_PARTIAL = '#D97706'
    C_BLOCK = '#DC2626'
    C_ARROW = '#475569'
    C_BORDER_INPUT = '#3B82F6'
    C_BORDER_PROF = '#10B981'
    C_BORDER_JUDGE = '#7C3AED'
    C_BORDER_OUT = '#EF4444'

    def box(x, y, w, h, color, border, label=None, fontsize=11, bold=False, radius=0.05):
        b = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={radius}",
                           facecolor=color, edgecolor=border, linewidth=2)
        ax.add_patch(b)
        if label:
            weight = 'bold' if bold else 'normal'
            ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                    fontsize=fontsize, fontweight=weight, color='#1E293B')
        return b

    def arrow(x1, y1, x2, y2, style='->', color=C_ARROW, lw=2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw))

    def darrow(x1, y1, x2, y2, color='#94A3B8'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                    linestyle='dashed'))

    # ── Title
    ax.text(7.5, 8.15, 'TransferJudge: Profiler-Judge LLM Framework',
            ha='center', va='center', fontsize=16, fontweight='bold', color='#1E293B')
    ax.plot([1, 14], [7.9, 7.9], color='#E94560', lw=2)

    # ── INPUT box
    box(0.3, 3.8, 2.6, 3.5, C_INPUT, C_BORDER_INPUT)
    ax.text(1.6, 7.0, 'INPUT', ha='center', fontsize=13, fontweight='bold', color=C_BORDER_INPUT)
    ax.text(1.6, 6.4, 'Source Reviews', ha='center', fontsize=9.5, color='#334155')
    ax.text(1.6, 6.05, '(Movies & TV, ≤30)', ha='center', fontsize=8, color='#64748B')
    ax.text(1.6, 5.5, 'Target Reviews', ha='center', fontsize=9.5, color='#334155')
    ax.text(1.6, 5.15, '(Books, ≤9, GT제외)', ha='center', fontsize=8, color='#64748B')
    ax.text(1.6, 4.55, 'User Behavior Data', ha='center', fontsize=9.5, color='#334155')
    ax.text(1.6, 4.2, '(rating, timestamp)', ha='center', fontsize=8, color='#64748B')

    # ── PROFILER box
    box(3.8, 4.2, 3.0, 3.1, C_PROFILER, C_BORDER_PROF)
    ax.text(5.3, 7.0, 'Profiler', ha='center', fontsize=13, fontweight='bold', color=C_BORDER_PROF)
    ax.text(5.3, 6.5, 'GPT-4o-mini', ha='center', fontsize=9, color='#64748B',
            style='italic')
    ax.text(5.3, 6.05, '프롬프트 기반 (FT 없음)', ha='center', fontsize=8.5, color='#475569')
    ax.text(5.3, 5.4, '6 Core Patterns 추출', ha='center', fontsize=9.5, color='#334155')
    ax.text(5.3, 5.0, '+ 추가 패턴 자유 발견', ha='center', fontsize=9, color='#334155')
    ax.text(5.3, 4.5, 'Output: JSON (~800 tok)', ha='center', fontsize=8.5, color='#64748B')

    # ── Arrow: Input → Profiler
    arrow(2.9, 5.8, 3.8, 5.8)
    ax.text(3.35, 6.05, '리뷰\n텍스트', ha='center', fontsize=7, color='#64748B')

    # ── TRANSFER JUDGE box (large)
    box(7.6, 2.8, 4.0, 4.5, C_JUDGE, C_BORDER_JUDGE)
    ax.text(9.6, 7.0, 'Transfer Judge', ha='center', fontsize=13, fontweight='bold',
            color=C_BORDER_JUDGE)
    ax.text(9.6, 6.5, 'Qwen3-14B-Instruct', ha='center', fontsize=9, color='#64748B',
            style='italic')
    ax.text(9.6, 6.1, 'QLoRA Fine-tuned', ha='center', fontsize=8.5, color='#475569')

    # ── Transfer Gate (inside Judge)
    box(8.0, 3.2, 3.2, 2.5, C_GATE, '#A78BFA', radius=0.04)
    ax.text(9.6, 5.45, 'Transfer Gate', ha='center', fontsize=11, fontweight='bold',
            color='#6D28D9')

    # Gate decisions
    ax.text(8.4, 4.85, '✓', ha='center', fontsize=12, color=C_TRANSFER, fontweight='bold')
    ax.text(9.0, 4.85, 'TRANSFER', ha='left', fontsize=9.5, color=C_TRANSFER, fontweight='bold')
    ax.text(8.4, 4.35, '△', ha='center', fontsize=12, color=C_PARTIAL, fontweight='bold')
    ax.text(9.0, 4.35, 'PARTIAL', ha='left', fontsize=9.5, color=C_PARTIAL, fontweight='bold')
    ax.text(8.4, 3.85, '✗', ha='center', fontsize=12, color=C_BLOCK, fontweight='bold')
    ax.text(9.0, 3.85, 'BLOCK', ha='left', fontsize=9.5, color=C_BLOCK, fontweight='bold')

    ax.text(10.5, 4.85, '그대로 전이', ha='left', fontsize=7.5, color='#64748B')
    ax.text(10.5, 4.35, '의미 변환 후 활용', ha='left', fontsize=7.5, color='#64748B')
    ax.text(10.5, 3.85, '완전 차단', ha='left', fontsize=7.5, color='#64748B')

    # ── Arrow: Profiler → Judge
    arrow(6.8, 5.8, 7.6, 5.8)
    ax.text(7.2, 6.05, '패턴\nJSON', ha='center', fontsize=7, color='#64748B')

    # ── OUTPUT box
    box(12.4, 3.8, 2.3, 3.5, C_OUTPUT, C_BORDER_OUT)
    ax.text(13.55, 7.0, 'OUTPUT', ha='center', fontsize=13, fontweight='bold', color=C_BORDER_OUT)
    ax.text(13.55, 6.35, 'Top-10 추천 리스트', ha='center', fontsize=9.5, color='#334155')
    ax.text(13.55, 5.85, '+ 추천 근거', ha='center', fontsize=9.5, color='#334155')
    ax.text(13.55, 5.35, '(Rationale)', ha='center', fontsize=9, color='#64748B')
    ax.text(13.55, 4.6, 'BLOCK 패턴 배제', ha='center', fontsize=9, color=C_BLOCK,
            fontweight='bold')
    ax.text(13.55, 4.15, 'Negative Transfer\n방지', ha='center', fontsize=9, color='#334155')

    # ── Arrow: Judge → Output
    arrow(11.6, 5.8, 12.4, 5.8)
    ax.text(12.0, 6.05, '판정+\n추천', ha='center', fontsize=7, color='#64748B')

    # ── Dashed: BLOCK → Output (excluded)
    darrow(11.3, 3.85, 12.8, 4.3, color=C_BLOCK)
    ax.text(12.0, 3.7, '차단', ha='center', fontsize=7.5, color=C_BLOCK, fontweight='bold')

    # ── Candidates box (below Judge)
    box(7.8, 1.8, 3.6, 0.7, '#F1F5F9', '#94A3B8')
    ax.text(9.6, 2.15, '후보 50개 (GT 1 + Negative 49)', ha='center', fontsize=9, color='#475569')
    darrow(9.6, 2.5, 9.6, 2.8, color='#94A3B8')

    # ── EVAL box (bottom)
    box(1.5, 0.3, 11.5, 1.1, C_EVAL, '#F59E0B')
    ax.text(7.25, 1.05, 'Evaluation: Leave-One-Out Protocol', ha='center', fontsize=11,
            fontweight='bold', color='#92400E')
    ax.text(7.25, 0.6, 'HR@1  |  HR@5  |  HR@10  |  NDCG@10  |  MRR    ·    '
            'Ablation: (a) Single LLM  (b) P-J Prompt  (c) Ours★  (d) w/o Gate  (e) CDR  (f) Raw Review',
            ha='center', fontsize=8, color='#78350F')

    fig.savefig(os.path.join(OUT, 'framework_diagram.png'), dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ framework_diagram.png")


# ──────────────────────────────────────────────
# 2. Cold-Start 개념도
# ──────────────────────────────────────────────
def draw_coldstart():
    fig, ax = plt.subplots(1, 1, figsize=(13, 5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5)
    ax.axis('off')

    # Title
    ax.text(6.5, 4.7, 'Cold-Start 문제와 Cross-Domain 전이 개념', ha='center',
            fontsize=14, fontweight='bold', color='#1E293B')

    # ── User icon area
    def user_box(x, y):
        circle = plt.Circle((x, y), 0.35, color='#DBEAFE', ec='#3B82F6', lw=2)
        ax.add_patch(circle)
        ax.text(x, y, '👤', ha='center', va='center', fontsize=16)

    user_box(1.2, 2.5)
    ax.text(1.2, 1.8, '사용자', ha='center', fontsize=10, fontweight='bold', color='#1E293B')

    # ── Source Domain (Movies)
    def box(x, y, w, h, color, ec):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                           facecolor=color, edgecolor=ec, linewidth=2)
        ax.add_patch(b)

    box(2.5, 1.5, 3.5, 2.5, '#D1FAE5', '#10B981')
    ax.text(4.25, 3.75, 'Source: Movies & TV', ha='center', fontsize=11,
            fontweight='bold', color='#059669')
    ax.text(4.25, 3.3, '🎬 45편 시청, 상세 리뷰', ha='center', fontsize=9.5, color='#334155')

    # Review bars (many)
    for i in range(8):
        bar_w = 2.2 - i * 0.1
        alpha = 1.0 - i * 0.08
        rect = FancyBboxPatch((3.15, 2.85 - i*0.17), bar_w, 0.12,
                               boxstyle="round,pad=0.02",
                               facecolor='#6EE7B7', alpha=alpha, ec='none')
        ax.add_patch(rect)
    ax.text(4.25, 1.65, '데이터 풍부 ✓', ha='center', fontsize=9,
            fontweight='bold', color='#059669')

    # Arrow from user to source
    ax.annotate('', xy=(2.5, 2.5), xytext=(1.55, 2.5),
                arrowprops=dict(arrowstyle='->', color='#64748B', lw=1.5))

    # ── Target Domain (Books)
    box(7.0, 1.5, 3.5, 2.5, '#FEE2E2', '#EF4444')
    ax.text(8.75, 3.75, 'Target: Books', ha='center', fontsize=11,
            fontweight='bold', color='#DC2626')
    ax.text(8.75, 3.3, '📚 3권 구매, 리뷰 거의 없음', ha='center', fontsize=9.5, color='#334155')

    # Review bars (few)
    for i in range(2):
        rect = FancyBboxPatch((7.65, 2.85 - i*0.17), 1.0, 0.12,
                               boxstyle="round,pad=0.02",
                               facecolor='#FCA5A5', alpha=0.8, ec='none')
        ax.add_patch(rect)
    ax.text(8.75, 2.2, '?', ha='center', fontsize=22, color='#FCA5A5', fontweight='bold')
    ax.text(8.75, 1.65, '데이터 부족 ✗ (Cold-Start)', ha='center', fontsize=9,
            fontweight='bold', color='#DC2626')

    # Arrow from user to target
    ax.annotate('', xy=(7.0, 2.5), xytext=(1.55, 2.5),
                arrowprops=dict(arrowstyle='->', color='#64748B', lw=1.5))

    # ── Transfer arrow (curved)
    ax.annotate('', xy=(7.0, 3.0), xytext=(6.0, 3.0),
                arrowprops=dict(arrowstyle='->', color='#7C3AED', lw=2.5,
                                connectionstyle='arc3,rad=0.3'))
    ax.text(6.5, 3.85, 'Cross-Domain\nTransfer', ha='center', fontsize=9,
            fontweight='bold', color='#7C3AED')

    # ── Solution box
    box(10.8, 1.5, 2.0, 2.5, '#EDE9FE', '#7C3AED')
    ax.text(11.8, 3.7, 'TransferJudge', ha='center', fontsize=10,
            fontweight='bold', color='#6D28D9')
    ax.text(11.8, 3.2, '유용한 패턴만\n선별 전이', ha='center', fontsize=9, color='#334155')
    ax.text(11.8, 2.5, '✓ SF 좋아함', ha='center', fontsize=8.5, color='#059669')
    ax.text(11.8, 2.15, '△ 영상미→묘사력', ha='center', fontsize=8.5, color='#D97706')
    ax.text(11.8, 1.8, '✗ 놀란 감독 팬', ha='center', fontsize=8.5, color='#DC2626')

    ax.annotate('', xy=(10.8, 2.8), xytext=(10.5, 2.8),
                arrowprops=dict(arrowstyle='->', color='#7C3AED', lw=2))

    # Bottom annotation
    ax.text(6.5, 0.9, 'Cold-Start 구간: Target 리뷰 5~10개 — Target 단독으로는 부족하되, '
            'CDR 효과를 측정할 수 있는 최적 구간', ha='center', fontsize=9,
            color='#475569', style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#F8FAFC', edgecolor='#CBD5E1'))

    fig.savefig(os.path.join(OUT, 'coldstart_concept.png'), dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("✓ coldstart_concept.png")


if __name__ == '__main__':
    draw_framework()
    draw_coldstart()
