import { DatePipe } from '@angular/common';
import { Component, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';
import { interval, switchMap, takeWhile } from 'rxjs';

import { ApiService } from '../core/api.service';
import { formatSekFromThousands } from '../core/format';
import { LEAD_STATUS_LABELS, Lead, LeadStatus, ScrapeParams, User } from '../core/models';
import { ScrapeDialog } from './scrape-dialog';

@Component({
  selector: 'app-leads-list',
  imports: [
    DatePipe,
    FormsModule,
    RouterLink,
    MatButtonModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressBarModule,
    MatSelectModule,
    MatTableModule,
    MatTooltipModule
  ],
  templateUrl: './leads-list.html',
  styleUrl: './leads-list.scss'
})
export class LeadsList implements OnDestroy {
  private api = inject(ApiService);
  private dialog = inject(MatDialog);
  private snack = inject(MatSnackBar);
  private route = inject(ActivatedRoute);

  readonly statusLabels = LEAD_STATUS_LABELS;
  readonly statuses = Object.keys(LEAD_STATUS_LABELS) as LeadStatus[];
  readonly columns = ['date', 'name', 'mobile', 'contact', 'revenue', 'employees', 'ai', 'status'];

  leads = signal<Lead[]>([]);
  counties = signal<string[]>([]);
  users = signal<User[]>([]);
  loading = signal(false);
  search = '';
  statusFilter = '';
  countyFilter = '';
  mobileOnly = false;
  contactOnly = false;

  scraping = signal(false);
  scrapeProgress = signal<{ processed: number; total: number | null; target: number | null } | null>(null);
  lastResult = signal<{
    newCount: number;
    updated: number;
    unchanged: number;
    skippedSni: number;
    finishedAt: Date;
  } | null>(null);
  private pollSub?: { unsubscribe: () => void };

  constructor() {
    const params = this.route.snapshot.queryParamMap;
    this.contactOnly = params.get('hasContact') === 'true';
    this.mobileOnly = params.get('hasMobile') === 'true';

    this.refresh();
    this.api.getCounties().subscribe((counties) => this.counties.set(counties));
    this.api.getUsers().subscribe((users) => this.users.set(users));
  }

  statusLabel(status: LeadStatus): string {
    return this.statusLabels[status];
  }

  formatRevenue(thousands: number | null | undefined): string {
    return formatSekFromThousands(thousands);
  }

  userColor(userId: string | null): string | null {
    return this.users().find((u) => u.id === userId)?.color ?? null;
  }

  userName(userId: string | null): string | null {
    return this.users().find((u) => u.id === userId)?.username ?? null;
  }

  refresh(): void {
    this.loading.set(true);
    this.api
      .getLeads({
        status: this.statusFilter,
        search: this.search,
        county: this.countyFilter,
        hasMobile: this.mobileOnly,
        hasContact: this.contactOnly
      })
      .subscribe({
        next: (leads) => {
          this.leads.set(leads);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
  }

  openScrapeDialog(): void {
    this.api.getSettings().subscribe((settings) => {
      const ref = this.dialog.open(ScrapeDialog, {
        data: { defaultIndustryCode: settings.defaultIndustryCode }
      });
      ref.afterClosed().subscribe((params: ScrapeParams | undefined) => {
        if (params) this.launchScrape(params);
      });
    });
  }

  private launchScrape(params: ScrapeParams): void {
    this.scraping.set(true);
    this.lastResult.set(null);
    this.scrapeProgress.set({ processed: 0, total: null, target: params.maxCompanies ?? null });

    this.api.startScrape(params).subscribe({
      next: ({ jobId }) => this.pollJob(jobId),
      error: (err) => {
        this.scraping.set(false);
        this.snack.open(err?.error?.error || 'Failed to start the search', 'OK', { duration: 4000 });
      }
    });
  }

  dismissResult(): void {
    this.lastResult.set(null);
  }

  private pollJob(jobId: string): void {
    this.pollSub = interval(1500)
      .pipe(
        switchMap(() => this.api.getScrapeStatus(jobId)),
        takeWhile((job) => job.status === 'running', true)
      )
      .subscribe({
        next: (job) => {
          const target = this.scrapeProgress()?.target ?? null;
          this.scrapeProgress.set({ processed: job.processed, total: job.total, target });

          if (job.status === 'done') {
            this.scraping.set(false);
            this.lastResult.set({
              newCount: job.new,
              updated: job.updated,
              unchanged: job.unchanged,
              skippedSni: job.skippedSni,
              finishedAt: new Date()
            });
            this.refresh();
          } else if (job.status === 'error') {
            this.scraping.set(false);
            this.snack.open(job.error || 'Error while scraping', 'OK', { duration: 6000 });
          }
        },
        error: () => this.scraping.set(false)
      });
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
  }
}
