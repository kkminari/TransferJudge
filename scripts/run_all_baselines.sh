#!/usr/bin/env bash
# Phase 4 — 7 conditions baseline 일괄 실행 스크립트
#
# 사용법:
#   bash scripts/run_all_baselines.sh smoke    # 3명만
#   bash scripts/run_all_baselines.sh full     # 100명 전체
#   bash scripts/run_all_baselines.sh openai   # OpenAI condition만 (a, b, g)
#   bash scripts/run_all_baselines.sh judge    # Judge condition만 (c, d)
#
# 환경 변수:
#   OPENAI_API_KEY 필요 (a/b/g용)
#   HF_TOKEN 필요 (Qwen3-14B base 다운로드)
#
# 산출:
#   results/ablation_{a_single,b_prompt,c_ours,d_no_gate,g_llm4cdr}.json

set -e

MODE="${1:-smoke}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results logs

if [[ "$MODE" == "smoke" ]]; then
    LIMIT=3
    SUFFIX="_smoke"
    echo "🧪 SMOKE MODE — 3명만 실행 (~$1 비용)"
elif [[ "$MODE" == "full" ]]; then
    LIMIT=0  # 0 = 전체
    SUFFIX=""
    echo "🚀 FULL MODE — 100명 전체 실행 (~$15-20 비용, ~6-10시간)"
elif [[ "$MODE" == "openai" ]]; then
    LIMIT=0
    SUFFIX=""
    echo "🌐 OPENAI-ONLY MODE — (a)(b)(g) 100명 전체"
elif [[ "$MODE" == "judge" ]]; then
    LIMIT=0
    SUFFIX=""
    echo "⚡ JUDGE-ONLY MODE — (c)(d) 100명 전체 (GPU)"
else
    echo "❌ 알 수 없는 MODE: $MODE"
    echo "Usage: $0 [smoke|full|openai|judge]"
    exit 1
fi

# OpenAI conditions: (a)(b)(g)
run_openai() {
    local cond="$1"
    local out="results/ablation_${cond}${SUFFIX}.json"
    if [[ -f "$out" ]] && [[ "$MODE" != "smoke" ]]; then
        echo "  ⏭️  $out 이미 존재, skip"
        return
    fi
    echo ""
    echo "═══════════════════════════════════════════"
    echo "🌐 OpenAI baseline: $cond"
    echo "═══════════════════════════════════════════"
    local limit_arg=""
    [[ "$LIMIT" -gt 0 ]] && limit_arg="--limit $LIMIT"
    python3 scripts/baseline_openai.py \
        --condition "$cond" \
        --output "$out" \
        $limit_arg \
        2>&1 | tee -a "logs/baseline_${cond}${SUFFIX}.log"
}

# Judge conditions: (c)(d)
run_judge() {
    local cond="$1"
    local out="results/ablation_${cond}${SUFFIX}.json"
    if [[ -f "$out" ]] && [[ "$MODE" != "smoke" ]]; then
        echo "  ⏭️  $out 이미 존재, skip"
        return
    fi
    echo ""
    echo "═══════════════════════════════════════════"
    echo "⚡ Judge inference: $cond"
    echo "═══════════════════════════════════════════"
    local limit_arg=""
    [[ "$LIMIT" -gt 0 ]] && limit_arg="--limit $LIMIT"
    python3 scripts/evaluate_judge.py \
        --condition "$cond" \
        --adapter checkpoints/judge_v1/adapter \
        --output "$out" \
        $limit_arg \
        2>&1 | tee -a "logs/eval_${cond}${SUFFIX}.log"
}

# 실행 순서 — OpenAI 먼저 (빠름), Judge 마지막 (오래 걸림)
if [[ "$MODE" == "openai" ]] || [[ "$MODE" == "smoke" ]] || [[ "$MODE" == "full" ]]; then
    run_openai "a_single"
    run_openai "b_prompt"
    run_openai "g_llm4cdr"
fi

if [[ "$MODE" == "judge" ]] || [[ "$MODE" == "smoke" ]] || [[ "$MODE" == "full" ]]; then
    run_judge "c_ours"
    run_judge "d_no_gate"
fi

echo ""
echo "✅ 완료. 결과:"
ls -lh results/ablation_*${SUFFIX}.json 2>/dev/null

echo ""
echo "다음: 결과 비교"
echo "  python3 scripts/visualize_results.py --results-dir results/"
