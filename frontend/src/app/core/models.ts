export interface FinancialYear {
  year: string | null;
  period: string | null;
  currency: string | null;
  revenue: number | null;
  resultEfterFinansnetto: number | null;
  ebitda: number | null;
  aretsResultat: number | null;
  summaTillgangar: number | null;
  egetKapital: number | null;
}

export interface KeyFigures {
  soliditet: number | null;
  vinstmarginal: number | null;
  kassalikviditet: number | null;
}

export type EmailStatus = 'not_contacted' | 'emailed' | 'replied' | 'unsubscribed';

export interface Lead {
  id: string;
  orgnr: string | null;
  name: string | null;
  contactPersonName: string | null;
  contactPersonRole: string | null;
  revenue: number | null;
  employees: number | null;
  county: string | null;
  municipality: string | null;
  bestEmail: string | null;
  bestPhone: string | null;
  mobile: string | null;
  foundWebsite: string | null;
  confidence: string | null;
  industryCode: string | null;
  industryName: string | null;
  sniCode: string | null;
  sniName: string | null;
  financials: FinancialYear[] | null;
  keyFigures: KeyFigures | null;
  status: LeadStatus;
  emailStatus: EmailStatus;
  assignedUserId: string | null;
  aiRecommendation: string | null;
  aiScore: number | null;
  aiReason: string | null;
  createdAt: string | null;
  callLogs?: CallLog[];
}

export type LeadStatus =
  | 'nouveau'
  | 'a_appeler'
  | 'appele'
  | 'interesse'
  | 'pas_interesse'
  | 'gagne';

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  nouveau: 'New',
  a_appeler: 'To call back',
  appele: 'Called',
  interesse: 'Interested',
  pas_interesse: 'Not interested',
  gagne: 'Won'
};

export interface CallLog {
  id: string;
  companyId: string;
  note: string | null;
  outcome: string | null;
  callDate: string | null;
  createdAt: string | null;
}

export interface DashboardSummary {
  totalLeads: number;
  totalRevenue: number;
  withContact: number;
  byStatus: Record<string, number>;
  topRevenue: { id: string; name: string; revenue: number; status: LeadStatus }[];
  priorityToCall: { id: string; name: string; aiScore: number | null; revenue: number | null }[];
}

export interface AppSettings {
  serperApiKey: string;
  groqApiKey: string;
  defaultIndustryCode: string;
  brevoApiKey: string;
  senderEmail: string;
  senderName: string;
  publicBaseUrl: string;
  webhookPath?: string;
}

export interface ScrapeParams {
  industryCode?: string;
  query?: string;
  county?: string;
  pages?: number;
  maxCompanies?: number;
  noEnrich?: boolean;
}

export interface ScrapeJob {
  status: 'running' | 'done' | 'error';
  processed: number;
  total: number | null;
  new: number;
  updated: number;
  unchanged: number;
  skippedSni: number;
  error: string | null;
}

export interface User {
  id: string;
  username: string;
  email: string | null;
  color: string;
  avatarUrl: string | null;
}

export interface FollowUpStep {
  afterDays: number;
}

export type CampaignStatus = 'draft' | 'sending' | 'sent';

export interface Campaign {
  id: string;
  name: string;
  subject: string;
  body: string;
  ownerId: string | null;
  ownerUsername?: string | null;
  ownerColor?: string | null;
  followUpCadence: FollowUpStep[];
  recipientFilter: { county?: string; status?: string; search?: string };
  status: CampaignStatus;
  createdAt: string | null;
  stats: {
    sent: number;
    delivered: number;
    bounced: number;
    opened: number;
    clicked: number;
    unsubscribed: number;
  };
}

export interface EmailSendRow {
  id: string;
  companyId: string;
  companyName: string | null;
  email: string;
  clicks: number;
  opens: number;
  lastEventAt: string | null;
}
