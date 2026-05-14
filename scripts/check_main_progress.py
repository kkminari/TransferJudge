#!/usr/bin/env python3
"""본 실험(Main Experiment) 진행 상태 자동 진단.

각 Phase의 산출물 존재 여부를 검사하여 현재 위치를 시각화하고
다음에 진행할 작업을 추천한다.

사용법:
  python scripts/check_main_progress.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 색상 코드
G = "\033[92m"  # green
Y = "\033[93m"  # yellow
R = "\033[91m"  # red
B = "\033[94m"  # blue
C = "\033[96m"  # cyan
W = "\033[0m"   # reset
BOLD = "\033[1m"

# 상태 아이콘
PASS = f"{G}✅{W}"
PROG = f"{Y}🟡{W}"
TODO = f"{R}⬜{W}"
BLOCK = f"{R}⚠️{W}"


def file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def count_files(pattern: str) -> int:
    return len(glob.glob(str(ROOT / pattern)))


def count_lines(path: str) -> int:
    p = ROOT / path
    if not p.exists():
        return 0
    with open(p) as f:
        return sum(1 for _ in f)


def check_phase_0() -> tuple[str, str]:
    """전제 조건 점검."""
    checks = []
    # API key
    env_file = ROOT / ".env"
    has_api = env_file.exists() and "OPENAI_API_KEY" in env_file.read_text()
    checks.append(("API key", has_api))
    # 데이터 분할
    has_data = all(
        file_exists(f"data/{name}_users.parquet") for name in ["train", "valid", "test"]
    )
    checks.append(("Data split", has_data))
    # Profiler/Teacher 스크립트 7-pattern 확인
    profiler_ok = "emotional_resonance" in (ROOT / "scripts/run_profiler.py").read_text()
    teacher_ok = "emotional_resonance" in (ROOT / "scripts/run_teacher.py").read_text()
    checks.append(("Profiler 7-pattern sync", profiler_ok))
    checks.append(("Teacher 7-pattern sync", teacher_ok))

    failed = [name for name, ok in checks if not ok]
    if not failed:
        return PASS, "전제 조건 모두 충족"
    else:
        return TODO, f"미달: {', '.join(failed)}"


def check_phase_1() -> tuple[str, str]:
    """Profiler 본 실행."""
    n_outputs = count_files("profiler_outputs/user_*.json")
    target = 1000
    if n_outputs == 0:
        return TODO, "아직 시작 안 함"
    elif n_outputs < target:
        return PROG, f"{n_outputs}/{target} 사용자 ({n_outputs/target*100:.1f}%)"
    else:
        # 7-pattern 완전성 검증
        keys_needed = {
            "genre_preference", "narrative_complexity", "pacing_preference",
            "quality_sensitivity", "brand_loyalty", "sensory_preference",
            "emotional_resonance",
        }
        ok = 0
        sample = glob.glob(str(ROOT / "profiler_outputs/user_*.json"))[:100]  # 표본만 빠르게
        for f in sample:
            try:
                d = json.load(open(f))
                if keys_needed.issubset(set(d.get("core_patterns", {}).keys())):
                    ok += 1
            except Exception:
                pass
        completeness = ok / len(sample) * 100 if sample else 0
        return PASS, f"{n_outputs}/{target} 완료 · 7-pattern 완전성 표본 {completeness:.0f}%"


def check_phase_2() -> tuple[str, str]:
    """Teacher Distillation."""
    train_lines = count_lines("data/teacher_train.jsonl")
    val_lines = count_lines("data/teacher_val.jsonl")
    train_target = 800
    val_target = 100

    if train_lines == 0 and val_lines == 0:
        return TODO, "아직 시작 안 함"
    elif train_lines < train_target * 0.95 or val_lines < val_target * 0.9:
        return PROG, f"train {train_lines}/{train_target}, val {val_lines}/{val_target}"
    else:
        return PASS, f"train {train_lines} · val {val_lines}"


def check_phase_3() -> tuple[str, str]:
    """QLoRA 파인튜닝."""
    best = ROOT / "checkpoints/judge_best"
    final = ROOT / "checkpoints/judge_final"
    metrics = ROOT / "logs/training_metrics.json"

    if not best.exists() and not final.exists():
        # 진행 중인지 확인
        latest = list(ROOT.glob("checkpoints/judge_checkpoint_*"))
        if latest:
            return PROG, f"학습 중 (checkpoint {len(latest)}개 저장됨)"
        return TODO, "아직 시작 안 함"
    elif best.exists():
        val_loss = "?"
        if metrics.exists():
            try:
                m = json.load(open(metrics))
                losses = [e.get("eval_loss") for e in m.get("log_history", []) if "eval_loss" in e]
                if losses:
                    val_loss = f"{min(losses):.4f}"
            except Exception:
                pass
        return PASS, f"judge_best 존재 · best val_loss={val_loss}"
    else:
        return PROG, "final만 존재, best 미확정"


def check_phase_4a() -> tuple[str, str]:
    """(c) Ours 평가."""
    f = ROOT / "results/ablation_c_ours.json"
    if not f.exists():
        return TODO, "아직 시작 안 함"
    try:
        d = json.load(open(f))
        n = len(d.get("per_user", d.get("results", [])))
        if n == 0:
            return PROG, "파일은 있으나 결과 비어있음"
        summary = d.get("summary", {})
        ndcg = summary.get("NDCG@10", "?")
        return PASS, f"{n} 사용자 · NDCG@10={ndcg}"
    except Exception as e:
        return BLOCK, f"파일 손상: {e}"


def check_phase_4b() -> tuple[str, str]:
    """(a)(b)(d)(f) Ablation."""
    conditions = ["a_single", "b_prompt", "d_no_gate", "f_raw"]
    done = sum(file_exists(f"results/ablation_{c}.json") for c in conditions)
    if done == 0:
        return TODO, "아직 시작 안 함"
    elif done < 4:
        missing = [c for c in conditions if not file_exists(f"results/ablation_{c}.json")]
        return PROG, f"{done}/4 완료 (남은 것: {', '.join(missing)})"
    else:
        return PASS, "4개 조건 모두 완료"


def check_phase_4c() -> tuple[str, str]:
    """(e) 전통 CDR."""
    f1 = ROOT / "results/ablation_e_traditional.json"
    f2 = ROOT / "results/ablation_e.json"
    if f1.exists() or f2.exists():
        return PASS, "전통 CDR 완료"
    return TODO, "아직 시작 안 함"


def check_phase_5a() -> tuple[str, str]:
    """Per-Pattern Ablation."""
    patterns = [
        "genre_preference", "narrative_complexity", "pacing_preference",
        "quality_sensitivity", "brand_loyalty", "sensory_preference",
        "emotional_resonance",
    ]
    done = sum(file_exists(f"results/per_pattern_{p}.json") for p in patterns)
    if done == 0:
        return TODO, "아직 시작 안 함"
    elif done < 7:
        return PROG, f"{done}/7 패턴 완료"
    else:
        heatmap = "results/per_pattern_heatmap.png"
        if file_exists(heatmap):
            return PASS, "7개 패턴 ablation + heatmap 완료"
        return PROG, "7개 패턴 완료, heatmap 미생성"


def check_phase_5b() -> tuple[str, str]:
    """Cold-Start 분석."""
    if file_exists("results/cold_start_analysis.csv"):
        return PASS, "Cold-Start segment 분석 완료"
    return TODO, "아직 시작 안 함"


def check_phase_6() -> tuple[str, str]:
    """결과 분석 + 통계."""
    has_table = file_exists("results/main_table.tex") or file_exists("results/main_table.csv")
    has_stats = file_exists("results/statistical_tests.csv")
    has_doc = file_exists("docs/Results_Analysis.md")
    score = sum([has_table, has_stats, has_doc])
    if score == 0:
        return TODO, "아직 시작 안 함"
    elif score < 3:
        missing = []
        if not has_table: missing.append("main_table")
        if not has_stats: missing.append("statistical_tests")
        if not has_doc: missing.append("Results_Analysis.md")
        return PROG, f"{score}/3 산출 (남은 것: {', '.join(missing)})"
    return PASS, "분석 + 통계 + 문서 모두 완료"


def check_phase_7() -> tuple[str, str]:
    """논문 초고."""
    candidates = ["docs/thesis_draft_v1.md", "docs/thesis_draft.md", "paper/thesis_draft_v1.tex"]
    for c in candidates:
        if file_exists(c):
            return PASS, f"초고 존재: {c}"
    return TODO, "아직 시작 안 함"


PHASES = [
    # (id, name, env, fn, cmd)
    ("0",   "전제 조건 점검",         "💻", check_phase_0,  "Tracker §Phase 0 체크리스트 확인"),
    ("1",   "Profiler 본 실행",       "💻", check_phase_1,  "python3 scripts/run_profiler.py --users data/train_users.parquet --reviews data/movies_reviews_filtered.parquet --output profiler_outputs/"),
    ("2",   "Teacher Distillation",   "💻", check_phase_2,  "python3 scripts/run_teacher.py --users data/train_users.parquet --profiles profiler_outputs/ --output data/teacher_train.jsonl --split train"),
    ("2.5", "GitHub Push → RunPod",   "🔄", None,           "Tracker §Phase 2.5 (.gitignore 갱신 → git push → RunPod clone)"),
    ("3",   "QLoRA 파인튜닝",         "☁️", check_phase_3,  "python3 scripts/train_judge_qlora.py --train data/teacher_train.jsonl --val data/teacher_val.jsonl --output_dir checkpoints/"),
    ("4a",  "Ablation (c) Ours",      "☁️", check_phase_4a, "python3 scripts/evaluate.py --condition c_ours --judge_ckpt checkpoints/judge_best/ --output results/ablation_c_ours.json"),
    ("4b",  "Ablation (a)(b)(d)(f)",  "💻☁️", check_phase_4b, "(a)(b)는 Mac, (d)(f)는 RunPod에서 실행 — Tracker §Phase 4b 참조"),
    ("4c",  "Ablation (e) 전통 CDR",  "☁️", check_phase_4c, "python3 scripts/train_eval_traditional_cdr.py --method emcdr --output results/ablation_e.json"),
    ("5a",  "Per-Pattern Ablation",   "☁️", check_phase_5a, "Tracker §Phase 5a 참조 (7개 패턴 ablation + heatmap)"),
    ("5b",  "RunPod→로컬 + Cold-Start", "💻", check_phase_5b, "RunPod에서 git push → Mac에서 git pull → python3 scripts/analyze_cold_start.py"),
    ("6",   "결과 분석 + 통계",       "💻", check_phase_6,  "python3 scripts/statistical_analysis.py + plot_results.py"),
    ("7",   "논문 초고",              "💻", check_phase_7,  "docs/thesis_draft_v1.md 작성"),
]


def detect_environment() -> str:
    """현재 실행 환경 감지: Mac 로컬 / RunPod GPU / 기타 Linux."""
    import platform
    system = platform.system()
    if system == "Darwin":
        return "💻 Mac 로컬"
    # Linux: GPU 있으면 RunPod 추정
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            gpu_name = torch.cuda.get_device_name(0)
            return f"☁️ GPU 환경 ({gpu_name}, {vram_gb:.1f}GB VRAM)"
    except Exception:
        pass
    return f"🖥️ {system}"


def main() -> None:
    env = detect_environment()
    print(f"\n{BOLD}{'='*78}{W}")
    print(f"{BOLD}🚀 TransferJudge 본 실험 진행 상태{W}      {C}현재 환경: {env}{W}")
    print(f"{BOLD}{'='*78}{W}\n")

    results = []
    for phase_id, name, env_label, fn, _ in PHASES:
        if fn is None:
            # Phase 2.5 같은 수동 단계 — 산출물로 추정
            # 2.5는 git push + RunPod clone이라 자동 감지 어려움 → Phase 3 시작됐으면 ✅
            try:
                ck = check_phase_3()
                if ck[0] == PASS or ck[0] == PROG:
                    status, detail = PASS, "RunPod 환경 가동 추정"
                else:
                    status, detail = TODO, "git push + RunPod 인스턴스 생성 필요"
            except Exception:
                status, detail = TODO, "수동 단계"
        else:
            try:
                status, detail = fn()
            except Exception as e:
                status, detail = BLOCK, f"진단 실패: {e}"
        results.append((phase_id, name, env_label, status, detail))
        print(f"[{status}] Phase {phase_id:<4} {env_label:<4} {BOLD}{name:<28}{W} {detail}")

    print()

    # 진행률 계산
    done = sum(1 for _, _, _, s, _ in results if s == PASS)
    total = len(results)
    bar_len = 40
    filled = int(bar_len * done / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"{BOLD}진행률{W}: {C}{bar}{W} {done}/{total} 단계 ({done/total*100:.0f}%)")

    print()

    # 다음 작업 안내
    next_phase = None
    for phase_id, name, _, status, _ in results:
        if status != PASS:
            next_phase = phase_id
            break

    if next_phase is None:
        print(f"{G}{BOLD}🎉 모든 Phase 완료! 졸업 논문 작성 마무리만 남았습니다.{W}\n")
    else:
        info = next(p for p in PHASES if p[0] == next_phase)
        _, cur_name, cur_env, _, cmd = info
        # 환경 일치 여부 체크
        env_ok = True
        env_warn = ""
        if cur_env == "💻" and "Mac" not in env:
            env_ok = False
            env_warn = f"\n  {R}⚠️  이 Phase는 Mac 로컬에서 실행해야 합니다.{W}"
        elif cur_env == "☁️" and "Mac" in env:
            env_ok = False
            env_warn = f"\n  {R}⚠️  이 Phase는 RunPod GPU 환경에서 실행해야 합니다.{W}"

        print(f"{BOLD}{C}▶ 다음 작업{W}: Phase {next_phase} {cur_env} — {cur_name}")
        if env_warn:
            print(env_warn)
        print(f"{BOLD}  실행 명령{W}:")
        for line in cmd.split(" && "):
            print(f"    {Y}$ {line}{W}")
        print(f"\n{BOLD}  상세 가이드{W}: docs/MainExperiment_Tracker.md → Phase {next_phase} 섹션\n")

    # 환경 점검 (간단 정보)
    print(f"{BOLD}{'='*78}{W}")
    print(f"{BOLD}현재 상태 요약{W}")
    print(f"{BOLD}{'='*78}{W}")
    print(f"  📂 작업 디렉토리   : {ROOT}")
    print(f"  🖥️  실행 환경      : {env}")
    n_profiler = count_files("profiler_outputs/user_*.json")
    n_results = count_files("results/ablation_*.json")
    print(f"  📊 Profiler 출력  : {n_profiler}/1000")
    print(f"  📊 Ablation 결과  : {n_results}/6")
    has_ckpt = (ROOT / "checkpoints/judge_best").exists()
    print(f"  💾 Judge 체크포인트: {'✅ 존재' if has_ckpt else '⬜ 없음'}")
    print()
    print(f"  💡 도움말: docs/MainExperiment_Tracker.md 의 Phase별 상세 가이드 참조")
    print()


if __name__ == "__main__":
    main()
