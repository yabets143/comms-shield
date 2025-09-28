import sys
from PIL import Image
import numpy as np
from scipy.stats import chi2

# Import the steganography-tools detector
from stegano import lsb  # assuming you installed `steganography-tools`

# -----------------------------
# Chi-square helpers
# -----------------------------
def lsb_counts(img_arr):
    if img_arr.ndim == 2:  # grayscale
        bits = img_arr & 1
        return np.bincount(bits.ravel(), minlength=2).astype(int)
    else:
        counts = []
        for c in range(img_arr.shape[2]):
            bits = img_arr[..., c] & 1
            counts.append(np.bincount(bits.ravel(), minlength=2).astype(int))
        return counts

def chi2_stat(counts):
    total = counts.sum()
    expected = np.array([total/2.0, total/2.0])
    chi2v = ((counts - expected)**2 / expected).sum()
    pval = chi2.sf(chi2v, df=1)
    return chi2v, pval

# -----------------------------
# RS Analysis (basic)
# -----------------------------
def rs_analysis(img_arr):
    channel = img_arr[..., 0].astype(int)  # red channel
    pairs = channel.flatten()[::2], channel.flatten()[1::2]
    diffs = np.abs(pairs[0] - pairs[1])
    reg = np.sum(diffs % 2 == 0)
    sing = np.sum(diffs % 2 == 1)
    return reg, sing

# -----------------------------
# Steganography-tools detection
# -----------------------------
def stegano_detect(path):
    """
    Use stegano LSB reveal as a detection attempt.
    If it returns non-empty or non-trivial data, we flag it.
    """
    try:
        secret = lsb.reveal(path)
        if secret:
            return True, secret
        return False, None
    except Exception:
        return False, None

# -----------------------------
# Main analyze function
# -----------------------------
def analyze(path, verbose=True):
    img = Image.open(path)
    mode = img.mode
    if mode not in ("RGB", "L"):
        img = img.convert("RGB")
    arr = np.array(img)
    counts = lsb_counts(arr)

    results = []
    if isinstance(counts[0], np.integer) if hasattr(counts[0], "dtype") else False:
        chi2v, pval = chi2_stat(counts)
        results.append(("L", counts, chi2v, pval))
    else:
        channel_names = ["R","G","B"]
        for chname, c in zip(channel_names, counts):
            chi2v, pval = chi2_stat(c)
            results.append((chname, c, chi2v, pval))
        flat = sum(counts)
        chi2v_all, pval_all = chi2_stat(flat)
        results.append(("ALL", flat, chi2v_all, pval_all))

    # RS analysis
    reg, sing = rs_analysis(arr)

    # Stegano-tools check
    steg_detected, secret = stegano_detect(path)

    if verbose:
        print(f"File: {path}")
        print(f"Image mode: {mode}, shape: {arr.shape}")
        for ch, c, chi2v, pval in results:
            n0, n1 = int(c[0]), int(c[1])
            total = n0 + n1
            print(f"Channel {ch}: n0={n0} n1={n1} total={total} chi2={chi2v:.4f} p={pval:.4e}")

        # Decision
        if steg_detected:
            print("\n=> DETECTION (stegano-tools): hidden data detected")
            print(f"Extracted (partial) secret: {secret[:50]}...")
        elif pval_all < 0.01 or reg != sing:
            print("\n=> DETECTION: likely hidden data (statistical)")
        elif pval_all < 0.10:
            print("\n=> SUSPICIOUS: possible hidden data")
        else:
            print("\n=> CLEAN")

        print(f"RS analysis: Regular={reg}, Singular={sing}")

    return results, (reg, sing), (steg_detected, secret)

# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python stegscan.py <image.png>")
        sys.exit(1)
    analyze(sys.argv[1])
