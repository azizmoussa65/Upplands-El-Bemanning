import { Routes } from '@angular/router';

import { authGuard } from './core/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login').then((m) => m.Login)
  },
  {
    path: '',
    loadComponent: () => import('./layout/layout').then((m) => m.Layout),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./dashboard/dashboard').then((m) => m.Dashboard)
      },
      {
        path: 'leads',
        loadComponent: () => import('./leads/leads-list').then((m) => m.LeadsList)
      },
      {
        path: 'leads/:id',
        loadComponent: () => import('./leads/lead-detail').then((m) => m.LeadDetail)
      },
      {
        path: 'settings',
        loadComponent: () => import('./settings/settings').then((m) => m.SettingsPage)
      },
      {
        path: 'users',
        loadComponent: () => import('./users/users-list').then((m) => m.UsersList)
      },
      {
        path: 'campaigns',
        loadComponent: () => import('./campaigns/campaigns-list').then((m) => m.CampaignsList)
      },
      {
        path: 'campaigns/new',
        loadComponent: () => import('./campaigns/campaign-editor').then((m) => m.CampaignEditor)
      },
      {
        path: 'campaigns/:id',
        loadComponent: () => import('./campaigns/campaign-detail').then((m) => m.CampaignDetail)
      },
      {
        path: 'campaigns/:id/opens',
        loadComponent: () => import('./campaigns/campaign-events').then((m) => m.CampaignEvents)
      },
      {
        path: 'campaigns/:id/clicks',
        loadComponent: () => import('./campaigns/campaign-events').then((m) => m.CampaignEvents)
      }
    ]
  },
  { path: '**', redirectTo: '' }
];
