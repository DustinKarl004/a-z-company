<script setup>
import { computed, nextTick, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { ApiError } from "../api/client";
import { defaultRouteForRole } from "../utils/roleRoute";

const email = ref("");
const password = ref("");
const digits = ref(["", "", "", "", "", ""]);
const digitRefs = ref([]);
const needsTotpCode = ref(false);
const error = ref("");
const loading = ref(false);
const showPassword = ref(false);

const totpCode = computed(() => digits.value.join(""));

const auth = useAuthStore();
const router = useRouter();

function setDigitRef(el, index) {
  digitRefs.value[index] = el;
}

function focusDigit(index) {
  digitRefs.value[index]?.focus();
}

function onDigitInput(index, event) {
  const value = event.target.value.replace(/\D/g, "").slice(-1);
  digits.value[index] = value;
  if (value && index < 5) {
    nextTick(() => focusDigit(index + 1));
  }
  if (totpCode.value.length === 6) {
    onSubmit();
  }
}

function onDigitKeydown(index, event) {
  if (event.key === "Backspace" && !digits.value[index] && index > 0) {
    digits.value[index - 1] = "";
    nextTick(() => focusDigit(index - 1));
  } else if (event.key === "ArrowLeft" && index > 0) {
    focusDigit(index - 1);
  } else if (event.key === "ArrowRight" && index < 5) {
    focusDigit(index + 1);
  }
}

function onDigitPaste(event) {
  const pasted = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
  if (!pasted) return;
  event.preventDefault();
  digits.value = Array.from({ length: 6 }, (_, i) => pasted[i] || "");
  nextTick(() => focusDigit(Math.min(pasted.length, 5)));
  if (pasted.length === 6) {
    onSubmit();
  }
}

function backToPassword() {
  needsTotpCode.value = false;
  password.value = "";
  digits.value = ["", "", "", "", "", ""];
  error.value = "";
}

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value, totpCode.value);
    router.push(defaultRouteForRole(auth));
  } catch (e) {
    if (e instanceof ApiError && e.detail === "Valid authenticator code required") {
      if (needsTotpCode.value) {
        error.value = "Invalid code. Please try again.";
        digits.value = ["", "", "", "", "", ""];
        nextTick(() => focusDigit(0));
      } else {
        needsTotpCode.value = true;
        nextTick(() => focusDigit(0));
      }
    } else {
      error.value = e instanceof ApiError ? e.detail || "Login failed" : "Login failed";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <section class="left">
      <div class="left-inner">
        <div class="inv-scene" aria-hidden="true">
          <div class="inv-icon inv-box">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 8l-9-5-9 5 9 5 9-5z" />
              <path d="M3 8v8l9 5 9-5V8" />
              <path d="M12 13v8" />
            </svg>
          </div>
          <div class="inv-icon inv-chart">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 3v18h18" />
              <path d="M7 16v-4M12 16V8m5 8v-6" />
            </svg>
          </div>
          <div class="inv-icon inv-truck">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 3h13v13H1z" />
              <path d="M14 8h4l3 3v5h-7z" />
              <circle cx="5.5" cy="18.5" r="1.8" />
              <circle cx="17.5" cy="18.5" r="1.8" />
            </svg>
          </div>
          <div class="inv-icon inv-clip">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 2h6v3H9z" />
              <path d="M6 4h12v18H6z" />
              <path d="M9 11l2 2 4-4" />
            </svg>
          </div>
          <span class="inv-orbit inv-orbit-a"></span>
          <span class="inv-orbit inv-orbit-b"></span>
        </div>
        <h1 class="brand-title">Z.A. Company</h1>
        <p class="brand-tagline">Stocks, sales, and profit — tracked per branch, every day.</p>
      </div>
    </section>

    <section class="right">
      <div class="auth-box">
        <div class="right-logo">
          <img class="right-logo-img" src="/logo.png" alt="Z.A. Company" />
        </div>

        <template v-if="!needsTotpCode">
          <h2 class="welcome-title">Welcome back</h2>
          <p class="welcome-subtitle">Sign in to manage your branch.</p>

          <div class="tab-sw">
            <button class="tab-btn active" type="button">sign in</button>
          </div>

          <form class="fp active" @submit.prevent="onSubmit">
            <div class="fg">
              <label for="email">Email address</label>
              <input
                id="email"
                v-model="email"
                type="email"
                maxlength="254"
                autocomplete="email"
                placeholder="Email address"
                required
              />
            </div>

            <div class="fg">
              <label for="password">Password</label>
              <div class="inpw">
                <input
                  id="password"
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  class="tpw"
                  :aria-label="showPassword ? 'Hide password' : 'Show password'"
                  @click="showPassword = !showPassword"
                >
                  <svg v-if="showPassword" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                  <svg v-else width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </button>
              </div>
            </div>

            <button class="btn-p" type="submit" :disabled="loading">
              <span v-if="loading" class="spinner" aria-hidden="true"></span>
              {{ loading ? "Signing in..." : "Sign in" }}
            </button>

            <p v-if="error" class="error-message">{{ error }}</p>
          </form>
        </template>

        <template v-else>
          <div class="totp-icon" aria-hidden="true">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="5" y="11" width="14" height="10" rx="2" />
              <path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
          </div>
          <h2 class="welcome-title">Two-factor authentication</h2>
          <p class="welcome-subtitle">Enter the 6-digit code from your authenticator app for <strong>{{ email }}</strong>.</p>

          <form class="fp active" @submit.prevent="onSubmit">
            <div class="otp-row" @paste="onDigitPaste">
              <input
                v-for="(digit, i) in digits"
                :key="i"
                :ref="(el) => setDigitRef(el, i)"
                v-model="digits[i]"
                type="text"
                inputmode="numeric"
                autocomplete="one-time-code"
                maxlength="1"
                class="otp-box"
                :class="{ 'otp-box-error': error }"
                :autofocus="i === 0"
                @input="onDigitInput(i, $event)"
                @keydown="onDigitKeydown(i, $event)"
              />
            </div>

            <button class="btn-p" type="submit" :disabled="loading || totpCode.length < 6">
              <span v-if="loading" class="spinner" aria-hidden="true"></span>
              {{ loading ? "Verifying..." : "Verify and sign in" }}
            </button>

            <p v-if="error" class="error-message">{{ error }}</p>

            <button type="button" class="back-link" @click="backToPassword">← Back to sign in</button>
          </form>
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
}

.left {
  flex: 0.85;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: #fff;
  position: relative;
  overflow: hidden;
}

.left::before {
  content: "";
  position: absolute;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: rgba(242, 169, 59, 0.12);
  top: -140px;
  right: -140px;
}

.left-inner {
  position: relative;
  z-index: 1;
  max-width: 380px;
  text-align: center;
}

.inv-scene {
  position: relative;
  height: 190px;
  margin-bottom: 1.75rem;
}

.inv-icon {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(2px);
  color: #fff;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.2);
  animation: inv-float 4.5s ease-in-out infinite;
}

.inv-box {
  left: 50%;
  top: 6px;
  transform: translateX(-50%);
  animation-delay: 0s;
}

.inv-chart {
  left: 8%;
  top: 78px;
  animation-delay: 0.9s;
}

.inv-truck {
  right: 6%;
  top: 84px;
  animation-delay: 0.4s;
}

.inv-clip {
  left: 30%;
  top: 148px;
  animation-delay: 1.4s;
}

.inv-orbit {
  position: absolute;
  border-radius: 50%;
  border: 1.5px dashed rgba(255, 255, 255, 0.25);
  animation: inv-spin linear infinite;
}

.inv-orbit-a {
  width: 220px;
  height: 220px;
  top: -15px;
  left: 50%;
  margin-left: -110px;
  animation-duration: 22s;
}

.inv-orbit-b {
  width: 150px;
  height: 150px;
  top: 20px;
  left: 50%;
  margin-left: -75px;
  animation-duration: 16s;
  animation-direction: reverse;
}

@keyframes inv-float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-14px) rotate(-4deg);
  }
}

.inv-box {
  animation-name: inv-float-box;
}

@keyframes inv-float-box {
  0%, 100% {
    transform: translateX(-50%) translateY(0) rotate(0deg);
  }
  50% {
    transform: translateX(-50%) translateY(-14px) rotate(3deg);
  }
}

@keyframes inv-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .inv-icon,
  .inv-orbit {
    animation: none;
  }
}

.brand-title {
  color: #fff;
  font-size: 1.9rem;
  margin-bottom: 0.75rem;
}

.brand-tagline {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.05rem;
  line-height: 1.5;
  margin: 0;
}

.right {
  flex: 1.15;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: 3rem;
}

.auth-box {
  width: 100%;
  max-width: 420px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 20px;
  box-shadow: var(--shadow);
  padding: 2.5rem 2.25rem;
}

.right-logo-img {
  display: block;
  width: 190px;
  height: 190px;
  margin: 0 auto 1rem;
  filter: drop-shadow(0 8px 20px rgba(0, 0, 0, 0.35));
}

.welcome-title {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 0.35rem;
}

.welcome-subtitle {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.95rem;
  margin: 0 0 1.75rem;
}

.tab-sw {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
}

.tab-btn {
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  padding: 0.5rem 0.25rem;
  font-size: 1.05rem;
  font-weight: 600;
  text-transform: capitalize;
  border-bottom: 2px solid transparent;
  border-radius: 0;
}

.tab-btn:hover {
  background: transparent;
  color: var(--color-text);
}

.tab-btn.active {
  color: var(--color-text);
  border-bottom-color: var(--color-accent);
}

.fg {
  margin-bottom: 1.35rem;
}

.fg label {
  font-size: 0.9rem;
}

.fg input {
  width: 100%;
  padding: 0.75rem 0.85rem;
  font-size: 1.02rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.fg input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.inpw {
  position: relative;
}

.inpw input {
  padding-right: 2.75rem;
}

.tpw {
  position: absolute;
  top: 50%;
  right: 0.35rem;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  border-radius: 6px;
  padding: 0;
}

.tpw:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.btn-p {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  margin-top: 0.75rem;
  padding: 0.85rem 1rem;
  font-size: 1.02rem;
  font-weight: 600;
}

.spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  text-align: center;
  margin-top: 1rem;
}

.totp-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  margin: 0 auto 1.1rem;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.otp-row {
  display: flex;
  justify-content: center;
  gap: 0.6rem;
  margin: 1.75rem 0 0.5rem;
}

.otp-box {
  width: 46px;
  height: 54px;
  text-align: center;
  font-size: 1.4rem;
  font-weight: 700;
  padding: 0;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.otp-box:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.otp-box-error {
  border-color: var(--color-danger);
}

.back-link {
  display: block;
  width: 100%;
  background: transparent;
  color: var(--color-text-muted);
  border: none;
  padding: 0.5rem;
  margin-top: 0.75rem;
  font-size: 0.9rem;
  text-align: center;
}

.back-link:hover {
  background: transparent;
  color: var(--color-text);
}

@media (max-width: 400px) {
  .otp-row {
    gap: 0.4rem;
  }

  .otp-box {
    width: 40px;
    height: 48px;
    font-size: 1.2rem;
  }
}

@media (max-width: 380px) {
  .right {
    padding: 1rem;
  }

  .auth-box {
    padding: 1.75rem 1rem;
  }

  .otp-row {
    gap: 0.3rem;
  }

  .otp-box {
    width: 34px;
    height: 44px;
    font-size: 1.05rem;
  }
}

@media (max-width: 860px) {
  .login-page {
    flex-direction: column;
  }

  .left {
    display: none;
  }

  .right {
    padding: 1.5rem;
  }

  .auth-box {
    padding: 2rem 1.5rem;
  }

  .right-logo-img {
    width: 140px;
    height: 140px;
  }
}
</style>
