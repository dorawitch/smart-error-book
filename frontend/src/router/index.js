import { createRouter, createWebHistory } from "vue-router";

import DashboardView from "../views/DashboardView.vue";
import QuestionBankView from "../views/QuestionBankView.vue";
import RecommendationView from "../views/RecommendationView.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard", name: "dashboard", component: DashboardView, meta: { title: "概览" } },
  { path: "/questions", name: "questions", component: QuestionBankView, meta: { title: "题库管理" } },
  { path: "/recommend", name: "recommend", component: RecommendationView, meta: { title: "智能推荐" } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
