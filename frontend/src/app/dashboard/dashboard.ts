import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { ApiService } from '../core/api.service';
import { AuthService, DEFAULT_BRAND_COLOR } from '../core/auth.service';
import { formatSekFromThousands } from '../core/format';
import { DashboardSummary, LEAD_STATUS_LABELS, LeadStatus } from '../core/models';

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, MatCardModule, MatIconModule, BaseChartDirective],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard {
  private api = inject(ApiService);
  private auth = inject(AuthService);

  summary = signal<DashboardSummary | null>(null);

  revenueChartData: ChartData<'bar'> = { labels: [], datasets: [{ data: [], label: 'Revenue (kSEK)', backgroundColor: this.userColor() }] };
  revenueChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { x: { ticks: { autoSkip: false } } }
  };

  statusChartData: ChartData<'doughnut'> = { labels: [], datasets: [{ data: [] }] };
  statusChartOptions: ChartConfiguration<'doughnut'>['options'] = { responsive: true };

  private statusColors: Record<string, string> = {
    nouveau: '#7fa8d9',
    a_appeler: '#f2c14e',
    appele: '#b0b0b0',
    interesse: '#4caf50',
    pas_interesse: '#c0605f',
    gagne: this.userColor()
  };

  private userColor(): string {
    return this.auth.currentUser()?.color || DEFAULT_BRAND_COLOR;
  }

  constructor() {
    this.api.getDashboardSummary().subscribe((summary) => {
      this.summary.set(summary);

      this.revenueChartData = {
        labels: summary.topRevenue.map((c) => c.name),
        datasets: [{ data: summary.topRevenue.map((c) => c.revenue), label: 'Revenue (kSEK)', backgroundColor: this.userColor() }]
      };

      const statusEntries = Object.entries(summary.byStatus);
      this.statusChartData = {
        labels: statusEntries.map(([k]) => LEAD_STATUS_LABELS[k as LeadStatus] ?? k),
        datasets: [
          {
            data: statusEntries.map(([, v]) => v),
            backgroundColor: statusEntries.map(([k]) => this.statusColors[k] || '#999')
          }
        ]
      };
    });
  }

  formatRevenue(thousands: number | null | undefined): string {
    return formatSekFromThousands(thousands);
  }
}
