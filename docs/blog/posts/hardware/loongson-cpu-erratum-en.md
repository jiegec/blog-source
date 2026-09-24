---
layout: post
date: 2026-09-24
tags: [loongson,loongarch,cpu,erratum]
categories:
    - hardware
---

# One CPU Atomic Instruction, One Packaging Infinite Loop: The Story of the Lost Update on LA664

[中文版本](loongson-cpu-erratum.md)

## TL;DR

In February 2026, [Wang Miao](github.com/shankerwangmiao) ran into something strange while packaging normaliz for Debian on a LoongArch server: the math software's built-in test kept timing out, stuck in an infinite loop that it could not escape. Following the code, the problem pointed to a very ordinary operation: OpenMP's `#pragma omp atomic` accumulating into a shared variable. The loop's exit condition required the accumulated value to equal a certain number, but the accumulated result was always less than that number, causing the infinite loop. Because the program was large and the code complex, we never managed to reduce it to a minimal example a human could understand, so the matter was shelved.

Half a year later, in August, Wang Miao came to me again, wanting to pick it back up. This time we took a different approach: instead of having a human locate the problem, we let AI find a minimal reproduction, with the human directing the AI's investigation. About two days later, we had a stable reproducer, and only then discovered the root cause: the CPU's atomic add instruction occasionally fails to be atomic. This meant we had found a new CPU erratum, and after Loongson learned of it, only two weeks passed before they found a fix with almost no performance loss and provided us with test firmware. We confirmed that the test firmware resolves the issue, and Loongson told us the firmware is expected to be released before National Day (October 1), at which point readers will be able to upgrade their firmware to fix the problem.

<!-- more -->

Now let us tell the whole story from beginning to end.

## Origins

[loong13](https://loong13.debian.net/) is a community-maintained port of Debian 13 stable to LoongArch, and Wang Miao is one of its maintainers. During the build and packaging process, normaliz's built-in test was found to get stuck in a loop that it could not exit, causing the packaging to time out. At the time we did not immediately find the root cause, so we had no choice but to skip this package. But since several other packages depend on normaliz, we could not keep skipping it forever, so in February we began to focus on investigating the problem. Previously, while building other packages, we had found hidden race conditions or memory-ordering issues in the code, and such problems are more likely to surface on LoongArch, which uses a weak memory model. So at first we guessed the cause might be a similar issue in this software. But once the investigation began, surprise, surprise, there was a surprise.

## The First Round of Investigation

The first round started from normaliz's source code. normaliz uses OpenMP to process data points in parallel. The problematic code snippet can be summarized as follows:

```c++
func (std::list<std::vector<int>> LatticePoints) {

  size_t nr_to_match = LatticePoints.size(); // input size
  size_t nr_points_matched = 0; // number of points already processed

  while (true) {
    size_t nr_points_done_in_this_round = 0; // number of points processed this round

    #pragma omp parallel
    {
      auto P = LatticePoints.begin(); // thread-private List pointer
      size_t ppos = 0; // thread-private List pointer position
      #pragma omp for
      for (ppp = 0...nr_to_match){

        if (skip_remaining) { // in certain cases skip_remaining is set, skipping unprocessed points
          continue;
        }

        // Based on the difference between ppos and ppp, move P to the position
        // pointed to by ppp and maintain ppos

        if ((*P)[0] == 0) { // means it has been processed
          continue;
        }

        #pragma omp atomic
        nr_points_matched++;
        #pragma omp atomic
        nr_points_done_in_this_round++;

        // process the object pointed to by P
        (*P)[0] = 0;
      }
    }

    // this break never gets executed
    if (nr_points_matched == nr_to_match)
      break;
  }

}
```

The gist of this code is: for a given `LatticePoints` list, the program processes each point in parallel. While processing each data point, some points may be temporarily skipped, requiring repeated passes until all data points have been processed. In this code, `nr_to_match` is the total number of data points, `nr_points_matched` is the number of points already processed, and `nr_points_done_in_this_round` is the number of points processed this round. The loop's termination condition is `nr_points_matched` equaling `nr_to_match`, i.e. all data points processed. The direct cause of the infinite loop is that `nr_points_matched` never reaches `nr_to_match`, so the loop cannot terminate. Using gdb, one can find that when this happens, every point in the entire `LatticePoints` list has been marked as processed, so `nr_points_matched` stops increasing, yet the loop's exit condition is never satisfied, so it just keeps looping. The question then becomes: why does the value of the counter `nr_points_matched` not match the actual number of processed data points. According to the code, the per-round increment of `nr_points_matched` should equal that of `nr_points_done_in_this_round`, because they are always atomically incremented together. But the actual output was not so: the two counters' values differ slightly, and the gap is unstable, with the result varying from run to run.

The first thing ruled out was a memory-ordering issue: this code does not rely on atomic variables to synchronize other variables; in other words, it operates on and reads only the atomic variables themselves the whole time, so from the code's perspective it is logically correct. The next suspicion was whether the OpenMP implementation was at fault: whether the atomic operations annotated with `#pragma omp atomic` really guarantee atomicity. From the disassembly, one can see the compiler generated the LoongArch64 `amadd.d` instruction for these atomic operations, as expected. To investigate this, we set up two additional `std::atomic` counters as controls, used alongside the original two, to see whether the results agreed. It turned out that the four counters' values (computed from the per-round increments) should have agreed, but in fact they showed random discrepancies. This hinted that the atomic add instruction loses updates under certain conditions.

However, testing the atomicity of the atomic add instruction with a simple atomic add program could not reproduce the lost update. To find a minimal reproducer, we simplified the aforementioned normaliz processing logic into a similar test program, which also could not reproduce the problem. So we had to keep commenting out computation steps in normaliz's actually-running code, trying to find the minimal condition that triggers the lost atomic add. One bizarre phenomenon was that even after commenting out most of the computation steps, the problem persisted. Because the program was too complex, in the end we still could not find a minimal code snippet that reliably reproduced the lost atomic add.

## The Second Round of Investigation

Six months later, the problem remained unsolved. With the disclosure of the [LoongLeak/LoongBleed vulnerabilities](./loongleak-loongbleed.md), the lost atomic add in normaliz came back into our view. This time, we tried to use AI to assist the investigation. The method was: first point out to the AI that the above normaliz code has an infinite-loop problem, ask the AI to confirm and reproduce it, and then find the possible cause. In the first round of conversation, the AI noticed the problematic loop but did not conclude that the atomic add instruction was at fault. After that, we hinted to the AI that the problem exists only on LoongArch and not on other architectures, but the AI still could not give a definite conclusion. Finally, we directly told the AI the fact that we had already localized the problem to the atomic add, and asked it to reproduce it and provide a minimal reproducer. In that round of conversation, the AI eventually turned its attention to a `memcpy` call in the processing function, which was exactly the part overlooked in the first round: `memcpy`'s implementation lives in glibc, and glibc chooses the optimal implementation based on currently available hardware features; if the hardware supports a vector instruction set (LSX/LASX on LoongArch), glibc's `memcpy` will use the corresponding vector instructions to accelerate memory copying. And it was precisely these vectorized memory copies that triggered the lost atomic add on LoongArch64. Two days later, the AI produced a minimal program that reliably reproduces the problem.

## Expanding the Scope

After discovering that the atomic add instruction can lose updates, we had new questions: first, is only atomic add affected, or do other atomic instructions have the same problem; second, do other memory operations also trigger similar problems.

For the first question, we first investigated the CAS instruction, because it can be used to implement atomic addition, making it easy to tell whether something goes wrong. It turned out that CAS also has the problem under the same conditions. For other atomic instructions, such as atomic swap, atomic max, atomic min, atomic bitwise AND, atomic bitwise OR, and so on, since even a lost update is not easy to detect from the result, we did not verify them at first. For example, if a lost update happens during an atomic max, then as long as the operation that updated the maximum was not lost, the result is correct.

After much thought, we finally found a verification scheme: to check whether such instructions lose updates, we recorded the result of every operation and verified afterward. Take atomic max as an example: if you atomically take the max over the numbers 1 to n in parallel, the final result should be n. Each atomic max modifies the memory and also returns the old maximum. For an operation with input k, if the returned old value is less than k, then this operation updated the maximum. Atomicity guarantees that the return values of all operations that updated the maximum will not repeat. If a repeat occurs, then a lost update of the atomic instruction occurred. Verification showed that these atomic instructions all lose updates under the same conditions.

For the second question, we found in testing that only LASX vectorized memory reads (`xvld`) trigger the lost atomic instruction; normal scalar reads and LSX vectorized memory reads (`vld`) do not trigger the problem. Later, [Rong "Mantle" Bao](https://github.com/CSharperMantle) independently discovered that when the memory address of the atomic variable and the read memory address have a particular positional relationship, normal scalar reads can also trigger the lost atomic instruction, meaning the problem can occur even without LASX, just with lower probability. These complex triggering conditions explain why this problem went undiscovered for so long.

## Specific Conclusions

Before presenting the specific conclusions, let us first introduce the background: Loongson's 3C6000/S and 3A6000 use the LA664 core, whose instruction set is LoongArch64 with SIMD extensions; of these, the 128-bit SIMD extension is called LSX and the 256-bit one is called LASX. The earlier LA464 core (such as the 3A5000) does not have this problem. LASX includes the memory-read instruction `xvld`, which can read 32 bytes at a time into a vector register. Loongson's atomic instructions can be summarized as `am<OP>[_db].<width>`, where `<OP>` is the specific atomic operation, such as `amadd`, `amcas`, `amswap`, `ammax`, `amxor`, `amand`, `amor`, etc.; `[_db]` indicates whether it carries a data barrier (db); and `<width>` is the data width of the operation, e.g. `.d` for 64-bit and `.w` for 32-bit.

Summarizing the experimental results, reproducing a lost atomic operation requires all three of the following conditions at once:

- The threads run on different physical cores (i.e. not two SMT logical cores on the same physical core);
- These threads perform atomic operations without a data barrier on the same address;
- At least one of the threads interleaves memory reads between atomic operations.

Here, the memory-read operation can be the LASX vectorized memory read `xvld`; when the read memory address and the atomic operation's memory address have a particular positional relationship, the memory-read operation can also be an ordinary scalar read.

## Reproduction and Measurement

The minimal reproducer came from the AI's simplification of the normaliz code. Each normaliz data point is 2208 bytes, i.e. 276 `uint64_t`s. Two threads traverse these points in shards; for each point they first do a vectorized memory copy (`memcpy`), then do one relaxed atomic add on each of three shared counters (corresponding to the amadd instruction without a data barrier). After each round, they check whether the three counters are equal; if not, a lost update occurred.

On a 3C6000/S, using two different physical cores (e.g. CPU0 and CPU2), 2208 bytes per point, 200 rounds per trial, and 30 trials in total, we obtained the following results:

| Atomic Op    | Both do LASX copy | Both do LASX read | One side LASX copy |
|--------------|------------------:|------------------:|-------------------:|
| `amadd.d`    |               67% |              100% |                53% |
| `amadd.w`    |               73% |              100% |                67% |
| `amcas.d`    |               77% |               97% |                17% |
| `amcas_db.d` |                0% |                0% |                 0% |
| `ammax.d`    |               43% |              100% |                50% |
| `amswap.d`   |               53% |              100% |                53% |

The percentages in the table are "the proportion of trials that failed out of 30 trials". One can see that "both do LASX read" most easily triggers the problem, with a probability of almost 100%; `amcas_db.d` with db is always 0% under the same conditions.

## An Aside: Why AOSC Could No Longer Reproduce It Later

During the process of reproducing this problem, there was a small aside, and it is also the most interesting part of the whole story. When the problem was first discovered in February, both AOSC OS and Debian could reproduce the normaliz infinite loop. But when we re-investigated in August, AOSC could not reproduce it no matter what, while Debian still could. At the time we did not know why this inconsistency occurred, and just kept experimenting on Debian.

Later, as the AI localized the problem to `memcpy`, we understood the reason. The Core 13 release that AOSC shipped after February had mistakenly disabled the `--enable-multi-arch` option in glibc, so the system `memcpy` no longer took the LASX acceleration path; whereas Debian's glibc enables vector acceleration normally, so its `memcpy` uses LASX. In February, both AOSC and Debian used the LASX acceleration path; by August, AOSC's `memcpy` no longer used LASX acceleration, so naturally it could not be triggered. On Debian, disabling LASX acceleration with `GLIBC_TUNABLES=glibc.cpu.hwcaps=-LASX` also stopped the problem from triggering.

So once AOSC releases Core 14 and re-enables the `--enable-multi-arch` option, the problem will reappear. Considering how commonly `memcpy` is used, the number of affected programs may be larger than we imagine, only because the trigger probability is low that it is hard to notice.

## Impact Analysis

Among the problematic atomic instructions, `ammax`, `ammin`, and the like are hard for compilers to generate because the C standard currently has no corresponding atomic operation interface; and `amcas` is an instruction newly added in LoongArch64 v1.1, so it is also not generated by compilers by default. The one that may have the largest impact is `amadd`, the atomic add instruction. This instruction is typically used for reference counting: if an increment of the reference count is lost, the count becomes smaller than the actual number of references, which may cause an object to be freed prematurely, leading to memory-safety problems such as use-after-free or double free. And the other triggering condition, vectorized memory reads, is easily triggered by functions like `memcpy`. We found that in the Rust standard library, the reference count of `std::sync::Arc` and the cloning of `std::sync::mpsc`'s `Sender` also use the `amadd` instruction without a data barrier. We constructed a safe Rust program; using either `Arc` or `mpsc` could make the program crash, manifesting as SIGABRT or glibc reporting heap corruption, which means a use-after-free occurred.

However, this problem is hard to use for a security attack. To trigger it, two threads must concurrently perform relaxed atomic operations on the same counter of the same object, and at least one of them must be doing a vectorized memory read. This triggering condition means the potential attacker and victim must be in the same process, and cannot be separated by process isolation, so it is hard to exploit unilaterally.

## Workarounds

In general, since in high-level language code developers have no control over the atomic instructions the compiler produces, application developers have no direct workaround. Software-level workarounds are mainly implemented through the compiler, i.e. the compiler no longer generates atomic instructions without a data barrier (`am<OP>.*`) but instead generates atomic instructions with a data barrier (`am<OP>_db.*`), or implements atomic operations using LL/SC loops. But for already-existing binaries, applying these workarounds requires a full recompile. Therefore, the cost of avoiding the problem at the software level is high.

## The Fix

After we reported it to Loongson, the fix came quickly: we emailed the problem to Loongson on August 26, 2026, and just two weeks later, on September 9, 2026, we received test firmware; both the 3A6000 and 3C6000/S returned to normal in our tests. Loongson told us this firmware is expected to be released before National Day (October 1).

The fix is to set bit 13 of MCSR24 to 1. MCSR24 is an internal CSR whose function is not described in the manual. After setting this bit, the lost update no longer occurs. Testing showed the performance loss is very small: single-core performance is unaffected, and multi-core performance drops only slightly.

If affected users cannot update the firmware for the time being, they can also choose to write this bit directly in the Linux kernel, which is equivalent to applying the firmware fix and avoids waiting for a motherboard firmware update.

## Conclusion

Looking back, this story began with a purely software problem: an infinite loop during packaging, a counter that occasionally miscounts. In the end it turned out to be an atomic add instruction in the CPU that is not atomic. From discovering the problem to finding the cause spanned half a year, yet the truly effective progress took only two days, with both AI and humans playing indispensable roles. The rest of the time went into confirming the problem, finding the triggering conditions, broadening the testing scope, and waiting for the firmware fix.

In fact, similar errata are very common in CPUs from all vendors. Interested readers can browse ARM's Software Developer Errata Notice for its cores, many of which involve memory-access or atomic instructions, with a few severe ones even causing the CPU to deadlock; but those that genuinely affect the user experience are actually very few. For such problems, rather than letting one suddenly surface someday in some complex system as an unstable error report, it is better to localize the specific cause and fix it as early as possible.

## Acknowledgements

This work was initiated and led by Wang Miao; I was responsible for reproduction and writing up the report. After we informed them that `amcas` also had the problem, [Rong "Mantle" Bao](https://github.com/CSharperMantle) discovered a similar CPU problem, which was fixed together. Thanks to Loongson's Chip R&D Department and Developer Community Operations Department, among others, for their efficient and professional work throughout the reporting and fixing process!
