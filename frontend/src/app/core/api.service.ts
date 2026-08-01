import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AppSettings,
  Campaign,
  CallLog,
  DashboardSummary,
  EmailSendRow,
  FollowUpStep,
  Lead,
  ScrapeJob,
  ScrapeParams,
  User
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api';

  getLeads(
    filters: {
      status?: string;
      county?: string;
      search?: string;
      hasMobile?: boolean;
      hasContact?: boolean;
    } = {}
  ): Observable<Lead[]> {
    const params: Record<string, string> = {};
    if (filters.status) params['status'] = filters.status;
    if (filters.county) params['county'] = filters.county;
    if (filters.search) params['search'] = filters.search;
    if (filters.hasMobile) params['hasMobile'] = 'true';
    if (filters.hasContact) params['hasContact'] = 'true';
    return this.http.get<Lead[]>(`${this.base}/leads`, { params });
  }

  getCounties(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/leads/counties`);
  }

  getLead(id: string): Observable<Lead> {
    return this.http.get<Lead>(`${this.base}/leads/${id}`);
  }

  updateLeadStatus(id: string, status: string): Observable<Lead> {
    return this.http.patch<Lead>(`${this.base}/leads/${id}`, { status });
  }

  assignLead(id: string, assignedUserId: string | null): Observable<Lead> {
    return this.http.patch<Lead>(`${this.base}/leads/${id}`, { assignedUserId });
  }

  markReplied(id: string): Observable<Lead> {
    return this.http.post<Lead>(`${this.base}/leads/${id}/mark-replied`, {});
  }

  addNote(id: string, note: string, outcome: string, callDate: string): Observable<CallLog> {
    return this.http.post<CallLog>(`${this.base}/leads/${id}/notes`, { note, outcome, callDate });
  }

  startScrape(params: ScrapeParams): Observable<{ jobId: string }> {
    return this.http.post<{ jobId: string }>(`${this.base}/leads/scrape`, params);
  }

  getScrapeStatus(jobId: string): Observable<ScrapeJob> {
    return this.http.get<ScrapeJob>(`${this.base}/leads/scrape/status/${jobId}`);
  }

  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.base}/dashboard/summary`);
  }

  getSettings(): Observable<AppSettings> {
    return this.http.get<AppSettings>(`${this.base}/settings`);
  }

  updateSettings(settings: Partial<AppSettings>): Observable<{ ok: boolean }> {
    return this.http.put<{ ok: boolean }>(`${this.base}/settings`, settings);
  }

  changePassword(currentPassword: string, newPassword: string): Observable<{ ok: boolean }> {
    return this.http.put<{ ok: boolean }>(`${this.base}/auth/password`, { currentPassword, newPassword });
  }

  recommend(id: string): Observable<Lead> {
    return this.http.post<Lead>(`${this.base}/leads/${id}/recommend`, {});
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.base}/users`);
  }

  createUser(username: string, password: string, email: string, color: string): Observable<User> {
    return this.http.post<User>(`${this.base}/users`, { username, password, email, color });
  }

  updateUser(id: string, changes: { email?: string; color?: string }): Observable<User> {
    return this.http.patch<User>(`${this.base}/users/${id}`, changes);
  }

  deleteUser(id: string): Observable<{ ok: boolean }> {
    return this.http.delete<{ ok: boolean }>(`${this.base}/users/${id}`);
  }

  uploadAvatar(id: string, file: File): Observable<User> {
    const formData = new FormData();
    formData.append('avatar', file);
    return this.http.post<User>(`${this.base}/users/${id}/avatar`, formData);
  }

  getCampaigns(): Observable<Campaign[]> {
    return this.http.get<Campaign[]>(`${this.base}/campaigns`);
  }

  getCampaign(id: string): Observable<Campaign> {
    return this.http.get<Campaign>(`${this.base}/campaigns/${id}`);
  }

  createCampaign(payload: {
    name: string;
    subject: string;
    body: string;
    followUpCadence: FollowUpStep[];
    recipientFilter: { county?: string; status?: string; search?: string };
  }): Observable<Campaign> {
    return this.http.post<Campaign>(`${this.base}/campaigns`, payload);
  }

  launchCampaign(id: string): Observable<{ ok: boolean; queued: number }> {
    return this.http.post<{ ok: boolean; queued: number }>(`${this.base}/campaigns/${id}/launch`, {});
  }

  deleteCampaign(id: string): Observable<{ ok: boolean }> {
    return this.http.delete<{ ok: boolean }>(`${this.base}/campaigns/${id}`);
  }

  previewRecipients(filter: { county?: string; status?: string; search?: string }): Observable<{ count: number }> {
    const params: Record<string, string> = {};
    if (filter.county) params['county'] = filter.county;
    if (filter.status) params['status'] = filter.status;
    if (filter.search) params['search'] = filter.search;
    return this.http.get<{ count: number }>(`${this.base}/campaigns/preview-recipients`, { params });
  }

  getCampaignSends(id: string, event?: 'opened' | 'clicked'): Observable<EmailSendRow[]> {
    const params: Record<string, string> = {};
    if (event) params['event'] = event;
    return this.http.get<EmailSendRow[]>(`${this.base}/campaigns/${id}/sends`, { params });
  }
}
