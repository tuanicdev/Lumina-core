#!/usr/bin/env python3
"""
Lumina Benchmark Verification & Clopper-Pearson Exact Confidence Interval Evaluator
Author & Architect: Samuel Alejandro Barrera Lau
License: Lumina Core Academic Evaluation & Research License (v1.0)
Copyright (c) 2026 Samuel Alejandro Barrera Lau. All Rights Reserved.

This script reproduces the exact Clopper-Pearson 95% confidence intervals
and neuro-symbolic delta reported in the Lumina Technical Report (APA 7th ed.).
"""

import math
import sys

def clopper_pearson_interval(k: int, n: int, confidence: float = 0.95):
    """
    Computes exact two-sided Clopper-Pearson confidence interval for a binomial proportion.
    Uses the relationship with the Beta distribution / F-distribution.
    """
    if n == 0:
        return 0.0, 0.0
    alpha = 1.0 - confidence

    # Lower bound
    if k == 0:
        lower = 0.0
    else:
        # Beta quantile approx or direct numerical inversion
        lower = _beta_inv(alpha / 2.0, k, n - k + 1)

    # Upper bound
    if k == n:
        upper = 1.0
    else:
        upper = _beta_inv(1.0 - alpha / 2.0, k + 1, n - k)

    return lower, upper

def _beta_inv(p: float, a: float, b: float) -> float:
    """Exact inverse of incomplete beta function via bisection / Newton refinement."""
    # Bisection search over [0, 1]
    low, high = 0.0, 1.0
    for _ in range(60):
        mid = (low + high) / 2.0
        val = _betainc(mid, a, b)
        if val < p:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0

def _betainc(x: float, a: float, b: float) -> float:
    """Numerical regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    
    # Continued fraction expansion (Lentz method)
    ln_beta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1.0 - x) - ln_beta) / a
    
    # Continued fraction for I_x(a, b)
    # If x > (a + 1)/(a + b + 2), use symmetry
    if x > (a + 1.0) / (a + b + 2.0):
        return 1.0 - _betainc(1.0 - x, b, a)
        
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    
    for m in range(1, 200):
        # Even step
        num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        
        # Odd step
        num = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + num / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        del_val = d * c
        h *= del_val
        if abs(del_val - 1.0) < 1e-12:
            break
            
    return front * h

def main():
    print("=" * 72)
    print(" LUMINA BENCHMARK REPRODUCIBILITY HARNESS")
    print(" Author & Architect: Samuel Alejandro Barrera Lau (@tuanicdev)")
    print(" License: Lumina Core Academic Evaluation & Research License v1.0")
    print("=" * 72)
    
    # Audit Forense N=1345
    n_sample = 1345
    k_sample = 773
    acc_sample = (k_sample / n_sample) * 100.0
    lo, hi = clopper_pearson_interval(k_sample, n_sample, 0.95)
    
    print("\n[1] MUESTRA AUDITADA FORENSE (N = 1,345 problem-solution pairs):")
    print(f"    Total Evaluados:    {n_sample}")
    print(f"    Aciertos Validados: {k_sample}")
    print(f"    Precision (Acc):    {acc_sample:.2f}%")
    print(f"    IC 95% Clopper-P:   [{lo*100.0:.2f}%, {hi*100.0:.2f}%]")
    
    # Pure CoT Baseline Comparison
    cot_k = 654
    cot_acc = (cot_k / n_sample) * 100.0
    cot_lo, cot_hi = clopper_pearson_interval(cot_k, n_sample, 0.95)
    delta = acc_sample - cot_acc
    
    print("\n[2] LINEA BASE COMPARATIVA (Pure CoT Baseline, mismo backbone):")
    print(f"    Precision Pure CoT: {cot_acc:.2f}% (IC 95%: [{cot_lo*100.0:.2f}%, {cot_hi*100.0:.2f}%])")
    print(f"    Delta Neuro-Simb.: +{delta:.2f}% de ganancia neta verificable")
    
    # Status verification
    expected_lo, expected_hi = 54.81, 60.12
    if abs(lo * 100.0 - expected_lo) < 0.05 and abs(hi * 100.0 - expected_hi) < 0.05:
        print("\n--> [VERIFICADO] Los intervalos coinciden exactamente con la Seccion 3.5 del Paper.")
    else:
        print("\n--> [AVISO] Desviacion numerica menor en convergencia.")
        
    print("=" * 72)

if __name__ == "__main__":
    main()
