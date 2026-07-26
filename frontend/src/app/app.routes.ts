import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'analyze', pathMatch: 'full' },
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then((m) => m.LoginComponent) },
  {
    path: 'register',
    loadComponent: () => import('./pages/register/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'analyze',
    loadComponent: () => import('./pages/analyze/analyze.component').then((m) => m.AnalyzeComponent),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'history',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/history/history.component').then((m) => m.HistoryComponent),
  },
  {
    path: 'history/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/history/history.component').then((m) => m.HistoryComponent),
  },
  { path: '**', redirectTo: 'analyze' },
];
