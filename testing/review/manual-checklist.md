# Manual Launch Checklist

Use this checklist before a wider release or after changes involving auth,
Supabase, administration, responsive layout, or deployment.

Do not test destructive actions against production unless the target data is
explicitly disposable and backed up.

## Public smoke test

- [ ] Landing page loads on phone and desktop.
- [ ] Practice, Scored Game, and Leaderboard links go to the expected pages.
- [ ] External PCTA marker link opens in a new tab.
- [ ] Logo, favicon, social preview metadata, and custom fonts load.
- [ ] About either has real content or is not offered as a separate destination.

## Practice game

- [ ] A photo appears before the timer starts counting down.
- [ ] Number input and slider remain synchronized.
- [ ] Enter submits from a keyboard.
- [ ] Empty Submit does nothing and does not stop the timer.
- [ ] A valid guess shows correct mile, direction, section, date, score, and map.
- [ ] A timeout scores zero and the game continues.
- [ ] Pinch-to-zoom works on the guess and result photos.
- [ ] Back/forward navigation during a game resets progress and shows the warning.
- [ ] Ten rounds produce ten recap rows.
- [ ] Recap thumbnails and map links work.
- [ ] Practice Again, Scored Game, and Leaderboard actions work.

## Accessibility and keyboard

- [ ] Tab order follows the visible interaction order.
- [ ] Focus is visible on every link, button, input, and slider.
- [ ] Number input and slider have meaningful accessible names.
- [ ] Timer and result feedback are understandable without color alone.
- [ ] Browser zoom at 200% does not hide controls.
- [ ] A keyboard-only player can complete all ten rounds.
- [ ] Reduced-motion preferences do not cause distracting animation.
- [ ] Text and controls remain readable in high-contrast settings.

## Responsive layouts

Check at approximately:

- [ ] 390 × 844 phone portrait.
- [ ] 844 × 390 phone landscape.
- [ ] 768 × 1024 tablet portrait.
- [ ] 1280 × 720 laptop.

At each size:

- [ ] No unintended horizontal scrolling.
- [ ] Submit and Next buttons remain visible and tappable.
- [ ] Slider labels do not overlap beyond recognition.
- [ ] Long trail names do not break leaderboard columns.
- [ ] Safe-area/notch spacing is acceptable on a real phone.

## Google authentication

- [ ] Signed-out Scored Game shows Google sign-in and Practice fallback.
- [ ] Google sign-in returns to the canonical `/game/` URL.
- [ ] Cancelled or failed OAuth returns to a usable state.
- [ ] A first-time user reaches profile setup.
- [ ] An existing user reaches the scored-game start screen.
- [ ] Sign out clears the session and returns to sign-in.

## Profile handling

- [ ] Required Trail Name and PCT Year validation is clear.
- [ ] About character count and saved value agree.
- [ ] Profile edits appear on leaderboard and hiker page.
- [ ] Very long names and years remain readable.
- [ ] HTML-like text displays literally and never creates markup.
- [ ] Empty, whitespace-heavy, emoji, apostrophe, and non-English values behave
      according to the chosen validation policy.

## Scored game

Use a designated test account and avoid cluttering production history.

- [ ] Completing a game saves exactly one session and ten guesses.
- [ ] Saved total, perfect count, and round scores match the browser display.
- [ ] Post-game rank matches the leaderboard's best-score-per-player rule.
- [ ] A failed save gives a useful message and does not falsely claim success.
- [ ] Rate-limit behavior and wording agree.
- [ ] The saved-game retention/cap policy is visible and recoverable.
- [ ] Refreshing or navigating back cannot duplicate a submission.

## Leaderboard and hiker pages

- [ ] All-Time ordering is descending and deduplicated by player.
- [ ] Optional 90-Day tab appears only when enabled.
- [ ] Current player's row is highlighted when signed in.
- [ ] Trail-name links open the correct hiker profile.
- [ ] Hiker best score, average, perfects, history, and badges agree.
- [ ] Empty profile and missing-ID states are friendly.
- [ ] Long values wrap without covering scores or controls.

## Admin read checks

- [ ] A non-admin account cannot access privileged data or actions.
- [ ] Admin Recent Games and Photo Stats load.
- [ ] Sorting and filtering Photo Stats produces credible results.
- [ ] Player search handles empty, partial, and unusual names.
- [ ] Site Settings display their current backend values.

## Admin mutation checks

Prefer staging. If production testing is unavoidable, create and use only an
explicitly disposable account.

- [ ] Rename confirmation identifies the correct player.
- [ ] Delete-games confirmation identifies the correct player and count.
- [ ] Delete-player confirmation clearly distinguishes profile data from the
      remaining OAuth account.
- [ ] Cancelling every confirmation leaves data unchanged.
- [ ] Photo statistics remain consistent after game deletion or are recalculated.
- [ ] A non-admin cannot call mutation RPCs directly.

## Supabase security review

Perform in staging when available.

- [ ] Anonymous callers cannot submit a scored game.
- [ ] A user cannot submit for another profile ID.
- [ ] Unknown photos and modified true miles are rejected.
- [ ] Totals and individual scores are calculated or verified server-side.
- [ ] Payloads must contain exactly ten unique valid photos.
- [ ] Public roles can read only the data required by public pages.
- [ ] Admin RPC execution is granted only to intended roles.

## Deployment

- [ ] `./testing/test.sh` passes.
- [ ] `bash build.sh` succeeds in the application project.
- [ ] Generated deploy pages correspond to current source.
- [ ] Photo files referenced by the CSV exist in `deploy/miles/`.
- [ ] Cloudflare deployment completes without unexpected deletions.
- [ ] Canonical production pages are smoke-tested after deploy.
- [ ] Supabase OAuth redirect allowlist still includes the canonical domain.

