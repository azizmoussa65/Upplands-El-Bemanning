import { DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { ApiService } from '../core/api.service';
import { EmailSendRow } from '../core/models';

@Component({
  selector: 'app-campaign-events',
  imports: [DatePipe, RouterLink, MatIconModule, MatTableModule],
  templateUrl: './campaign-events.html',
  styleUrl: './campaign-events.scss'
})
export class CampaignEvents {
  private route = inject(ActivatedRoute);
  private api = inject(ApiService);

  readonly columns = ['email', 'clicks', 'opens', 'companyName', 'lastEventAt'];

  rows = signal<EmailSendRow[]>([]);
  title = signal('Events');
  campaignId = '';

  constructor() {
    const segments = this.route.snapshot.url;
    const mode = segments[segments.length - 1]?.path === 'clicks' ? 'clicked' : 'opened';
    this.title.set(mode === 'clicked' ? 'Klick' : 'Öppnade');
    this.campaignId = this.route.snapshot.paramMap.get('id')!;

    this.api.getCampaignSends(this.campaignId, mode).subscribe((rows) => this.rows.set(rows));
  }
}
