import { DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTooltipModule } from '@angular/material/tooltip';

import { ApiService } from '../core/api.service';
import { Campaign } from '../core/models';

@Component({
  selector: 'app-campaigns-list',
  imports: [DatePipe, RouterLink, MatButtonModule, MatChipsModule, MatIconModule, MatTableModule, MatTooltipModule],
  templateUrl: './campaigns-list.html',
  styleUrl: './campaigns-list.scss'
})
export class CampaignsList {
  private api = inject(ApiService);
  private snack = inject(MatSnackBar);

  readonly columns = [
    'name',
    'subject',
    'owner',
    'sent',
    'delivered',
    'bounced',
    'opened',
    'clicked',
    'createdAt',
    'status',
    'actions'
  ];

  campaigns = signal<Campaign[]>([]);

  constructor() {
    this.refresh();
  }

  refresh(): void {
    this.api.getCampaigns().subscribe((campaigns) => this.campaigns.set(campaigns));
  }

  deleteCampaign(campaign: Campaign, event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    if (!confirm(`Delete campaign "${campaign.name}"?`)) return;
    this.api.deleteCampaign(campaign.id).subscribe({
      next: () => this.refresh(),
      error: (err) => this.snack.open(err?.error?.error || 'Could not delete campaign', 'OK', { duration: 4000 })
    });
  }
}
