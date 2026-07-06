<script setup>
import { onMounted, ref } from "vue";
import { listBranches } from "../api/branches";
import { createStaff, listStaff, updateStaff } from "../api/staff";
import { ApiError } from "../api/client";

const staff = ref([]);
const branches = ref([]);
const loading = ref(true);
const submitting = ref(false);
const error = ref("");

const form = ref({ name: "", email: "", password: "", branchId: "" });

function branchName(id) {
  return branches.value.find((b) => b.id === id)?.name || "—";
}

async function refresh() {
  loading.value = true;
  [staff.value, branches.value] = await Promise.all([listStaff(), listBranches()]);
  loading.value = false;
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await createStaff(form.value);
    form.value = { name: "", email: "", password: "", branchId: "" };
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create staff" : "Could not create staff";
  } finally {
    submitting.value = false;
  }
}

async function toggleActive(member) {
  await updateStaff(member.id, { is_active: !member.is_active });
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div>
    <h2>Staff</h2>

    <form class="card new-staff" @submit.prevent="onSubmit">
      <div class="field">
        <label for="staff-name">Name</label>
        <input id="staff-name" v-model="form.name" required />
      </div>
      <div class="field">
        <label for="staff-email">Email</label>
        <input id="staff-email" v-model="form.email" type="email" required />
      </div>
      <div class="field">
        <label for="staff-password">Password</label>
        <input id="staff-password" v-model="form.password" type="password" required minlength="8" />
      </div>
      <div class="field">
        <label for="staff-branch">Branch</label>
        <select id="staff-branch" v-model="form.branchId" required>
          <option disabled value="">Select a branch</option>
          <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
      </div>
      <button type="submit" :disabled="submitting">{{ submitting ? "Adding..." : "Add staff" }}</button>
      <p v-if="error" class="error-message">{{ error }}</p>
    </form>

    <div class="card">
      <table v-if="!loading">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Branch</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in staff" :key="s.id">
            <td>{{ s.name }}</td>
            <td>{{ s.email }}</td>
            <td>{{ branchName(s.branch_id) }}</td>
            <td>
              <span class="badge" :class="s.is_active ? 'active' : 'inactive'">
                {{ s.is_active ? "Active" : "Inactive" }}
              </span>
            </td>
            <td>
              <button class="secondary" @click="toggleActive(s)">
                {{ s.is_active ? "Deactivate" : "Activate" }}
              </button>
            </td>
          </tr>
          <tr v-if="staff.length === 0">
            <td colspan="5">No staff yet.</td>
          </tr>
        </tbody>
      </table>
      <p v-else>Loading...</p>
    </div>
  </div>
</template>

<style scoped>
.new-staff {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.new-staff button {
  grid-column: 1 / -1;
  width: fit-content;
}

.new-staff .error-message {
  grid-column: 1 / -1;
}
</style>
