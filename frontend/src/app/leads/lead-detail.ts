import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { ApiService } from '../core/api.service';
import { AuthService, DEFAULT_BRAND_COLOR } from '../core/auth.service';
import { formatPercent, formatSekFromThousands, yoyGrowthPercent } from '../core/format';
import { LEAD_STATUS_LABELS, Lead, LeadStatus, User } from '../core/models';

@Component({
  selector: 'app-lead-detail',
  imports: [
    DatePipe,
    FormsModule,
    RouterLink,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    BaseChartDirective
  ],
  templateUrl: './lead-detail.html',
  styleUrl: './lead-detail.scss'
})
export class LeadDetail {
  private route = inject(ActivatedRoute);
  private api = inject(ApiService);
  private snack = inject(MatSnackBar);
  private auth = inject(AuthService);

  readonly statusLabels = LEAD_STATUS_LABELS;
  readonly statuses = Object.keys(LEAD_STATUS_LABELS) as LeadStatus[];
  readonly outcomes = [
    { value: 'interesse', label: 'Interested' },
    { value: 'pas_interesse', label: 'Not interested' },
    { value: 'a_rappeler', label: 'Call back later' },
    { value: 'gagne', label: 'Won' },
    { value: 'sans_reponse', label: 'No answer' }
  ];

  lead = signal<Lead | null>(null);
  loading = signal(true);
  recommending = signal(false);
  users = signal<User[]>([]);
  markingReplied = signal(false);

  note = '';
  outcome = 'a_rappeler';
  callDate = new Date().toISOString().slice(0, 16);

  readonly financialsChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    plugins: { legend: { display: false } }
  };

  financialsChartData = computed<ChartData<'bar'>>(() => {
    const years = [...(this.lead()?.financials || [])].reverse();
    const color = this.auth.currentUser()?.color || DEFAULT_BRAND_COLOR;
    return {
      labels: years.map((y) => y.year ?? ''),
      datasets: [
        { data: years.map((y) => y.revenue ?? 0), label: 'Omsättning (tSEK)', backgroundColor: color }
      ]
    };
  });

  revenueGrowth = computed<number | null>(() => {
    const years = this.lead()?.financials;
    if (!years || years.length < 2) return null;
    return yoyGrowthPercent(years[0].revenue, years[1].revenue);
  });

  constructor() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.load(id);
    this.api.getUsers().subscribe((users) => this.users.set(users));
  }

  assignTo(userId: string): void {
    const lead = this.lead();
    if (!lead) return;
    this.api.assignLead(lead.id, userId || null).subscribe((updated) => {
      this.lead.set({ ...lead, ...updated, callLogs: lead.callLogs });
    });
  }

  markReplied(): void {
    const lead = this.lead();
    if (!lead) return;
    this.markingReplied.set(true);
    this.api.markReplied(lead.id).subscribe({
      next: (updated) => {
        this.markingReplied.set(false);
        this.lead.set({ ...lead, ...updated, callLogs: lead.callLogs });
        this.snack.open('Marked as replied — follow-ups stopped', 'OK', { duration: 3000 });
      },
      error: (err) => {
        this.markingReplied.set(false);
        this.snack.open(err?.error?.error || 'Could not update', 'OK', { duration: 4000 });
      }
    });
  }

  outcomeLabel(outcome: string | null): string {
    return this.outcomes.find((o) => o.value === outcome)?.label ?? outcome ?? '—';
  }

  formatRevenue(thousands: number | null | undefined): string {
    return formatSekFromThousands(thousands);
  }

  formatPercent(value: number | null | undefined): string {
    return formatPercent(value);
  }

  private load(id: string): void {
    this.loading.set(true);
    this.api.getLead(id).subscribe({
      next: (lead) => {
        this.lead.set(lead);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  changeStatus(status: LeadStatus): void {
    const lead = this.lead();
    if (!lead) return;
    this.api.updateLeadStatus(lead.id, status).subscribe((updated) => {
      this.lead.set({ ...lead, ...updated, callLogs: lead.callLogs });
    });
  }

  addNote(): void {
    const lead = this.lead();
    if (!lead || !this.note.trim()) return;

    const callDateIso = new Date(this.callDate).toISOString();
    this.api.addNote(lead.id, this.note, this.outcome, callDateIso).subscribe((log) => {
      this.lead.set({
        ...lead,
        callLogs: [log, ...(lead.callLogs || [])]
      });
      this.note = '';
      this.load(lead.id);
    });
  }

  recommend(): void {
    const lead = this.lead();
    if (!lead) return;
    this.recommending.set(true);
    this.api.recommend(lead.id).subscribe({
      next: (updated) => {
        this.recommending.set(false);
        this.lead.set({ ...lead, ...updated, callLogs: lead.callLogs });
      },
      error: (err) => {
        this.recommending.set(false);
        this.snack.open(err?.error?.error || 'AI recommendation error', 'OK', { duration: 4000 });
      }
    });
  }
}
