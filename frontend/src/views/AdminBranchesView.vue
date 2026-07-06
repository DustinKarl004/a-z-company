<script setup>
import { onMounted, ref } from "vue";
import { createBranch, listBranches } from "../api/branches";
import { ApiError } from "../api/client";

const branches = ref([]);
const name = ref("");
const error = ref("");
const submitting = ref(false);
const loading = ref(true);

async function refresh() {
  loading.value = true;
  branches.value = await listBranches();
  loading.value = false;
}

async function onSubmit() {
  error.value = "";
  submitting.value = true;
  try {
    await createBranch(name.value);
    name.value = "";
    await refresh();
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail || "Could not create branch" : "Could not create branch";
  } finally {
    submitting.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div>
    <h2>Branches</h2>

    <form class="card new-branch" @submit.prevent="onSubmit">
      <div class="field">
        <label for="branch-name">New branch name</label>
        <input id="branch-name" v-model="name" required placeholder="e.g. Quezon City" />
      </div>
      <button type="submit" :disabled="submitting">{{ submitting ? "Adding..." : "Add branch" }}</button>
      <p v-if="error" class="error-message">{{ error }}</p>
    </form>

    <div class="card">
      <table v-if="!loading">
        <thead>
          <tr>
            <th>Name</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in branches" :key="b.id">
            <td>{{ b.name }}</td>
            <td>{{ new Date(b.created_at).toLocaleDateString() }}</td>
          </tr>
          <tr v-if="branches.length === 0">
            <td colspan="2">No branches yet.</td>
          </tr>
        </tbody>
      </table>
      <p v-else>Loading...</p>
    </div>
  </div>
</template>

<style scoped>
.new-branch {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.new-branch .field {
  flex: 1;
  margin-bottom: 0;
}
</style>
