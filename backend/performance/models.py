from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class PerformanceIndicator(models.Model):
    """KPI and performance indicators for monitoring"""
    
    INDICATOR_TYPES = [
        ('quality', 'Quality'),
        ('efficiency', 'Efficiency'),
        ('effectiveness', 'Effectiveness'),
        ('customer_satisfaction', 'Customer Satisfaction'),
        ('process', 'Process Performance'),
        ('financial', 'Financial'),
        ('operational', 'Operational'),
    ]
    
    MEASUREMENT_FREQUENCY = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField()
    indicator_type = models.CharField(max_length=50, choices=INDICATOR_TYPES)
    measurement_method = models.TextField()
    formula = models.TextField(blank=True, help_text="Calculation formula if applicable")
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit_of_measure = models.CharField(max_length=50)
    frequency = models.CharField(max_length=20, choices=MEASUREMENT_FREQUENCY)
    responsible_person_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_indicators'
        unique_together = ['organization_id', 'code']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Measurement(models.Model):
    """Actual measurements and data collection"""
    
    STATUS_CHOICES = [
        ('on_target', 'On Target'),
        ('below_target', 'Below Target'),
        ('above_target', 'Above Target'),
        ('needs_attention', 'Needs Attention'),
    ]
    
    organization_id = models.IntegerField()
    indicator = models.ForeignKey(PerformanceIndicator, on_delete=models.CASCADE, related_name='measurements')
    measurement_date = models.DateField()
    actual_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    variance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    variance_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    comments = models.TextField(blank=True)
    measured_by_id = models.IntegerField(null=True, blank=True)
    evidence = models.FileField(upload_to='measurements/evidence/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'measurements'
        ordering = ['-measurement_date']
    
    def save(self, *args, **kwargs):
        if self.actual_value and self.target_value:
            self.variance = self.actual_value - self.target_value
            if self.target_value != 0:
                self.variance_percentage = (self.variance / self.target_value) * 100
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.indicator.code} - {self.measurement_date}"


class DataAnalysis(models.Model):
    """Analysis and evaluation of performance data"""
    
    ANALYSIS_TYPES = [
        ('trend', 'Trend Analysis'),
        ('comparative', 'Comparative Analysis'),
        ('root_cause', 'Root Cause Analysis'),
        ('predictive', 'Predictive Analysis'),
        ('statistical', 'Statistical Analysis'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    organization_id = models.IntegerField()
    title = models.CharField(max_length=200)
    analysis_type = models.CharField(max_length=50, choices=ANALYSIS_TYPES)
    period_start = models.DateField()
    period_end = models.DateField()
    objectives = models.TextField()
    methodology = models.TextField()
    findings = models.TextField()
    conclusions = models.TextField()
    recommendations = models.TextField()
    analyzed_by_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    ai_insights = models.JSONField(blank=True, null=True)
    ai_predictions = models.JSONField(blank=True, null=True)
    ai_anomalies = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_analyses'
        verbose_name_plural = 'Data analyses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.period_start} to {self.period_end})"


class InternalAudit(models.Model):
    """Internal audit management"""
    
    AUDIT_TYPES = [
        ('system', 'QMS System Audit'),
        ('process', 'Process Audit'),
        ('product', 'Product Audit'),
        ('compliance', 'Compliance Audit'),
        ('management', 'Management Audit'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    audit_code = models.CharField(max_length=50)
    audit_type = models.CharField(max_length=50, choices=AUDIT_TYPES)
    title = models.CharField(max_length=200)
    objectives = models.TextField()
    scope = models.TextField()
    criteria = models.TextField()
    planned_date = models.DateField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    lead_auditor_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    audit_report = models.TextField(blank=True)
    executive_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'internal_audits'
        unique_together = ['organization_id', 'audit_code']
        ordering = ['-planned_date']
    
    def __str__(self):
        return f"{self.audit_code} - {self.title}"


class AuditFinding(models.Model):
    """Individual audit findings and non-conformities"""
    
    FINDING_TYPES = [
        ('nc_major', 'Major Non-Conformity'),
        ('nc_minor', 'Minor Non-Conformity'),
        ('observation', 'Observation'),
        ('opportunity', 'Opportunity for Improvement'),
        ('conformity', 'Conformity'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('verified', 'Verified'),
        ('closed', 'Closed'),
    ]
    
    organization_id = models.IntegerField()
    audit = models.ForeignKey(InternalAudit, on_delete=models.CASCADE, related_name='findings')
    finding_number = models.CharField(max_length=50)
    finding_type = models.CharField(max_length=50, choices=FINDING_TYPES)
    clause_reference = models.CharField(max_length=100)
    description = models.TextField()
    evidence = models.TextField()
    root_cause = models.TextField(blank=True)
    immediate_action = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    responsible_person_id = models.IntegerField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    verification_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'audit_findings'
        ordering = ['finding_type', '-created_at']
    
    def __str__(self):
        return f"{self.finding_number} - {self.finding_type}"


class ManagementReview(models.Model):
    """Management review meetings and decisions"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    organization_id = models.IntegerField()
    organization_name = models.CharField(max_length=200)
    review_code = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    chairperson_id = models.IntegerField(null=True, blank=True)
    performance_results = models.TextField()
    customer_feedback = models.TextField(blank=True)
    process_performance = models.TextField(blank=True)
    nc_and_corrective_actions = models.TextField(blank=True)
    improvement_opportunities = models.TextField(blank=True)
    improvement_decisions = models.TextField(blank=True)
    qms_changes = models.TextField(blank=True)
    resource_needs = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    action_items = models.TextField(blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'management_reviews'
        unique_together = ['organization_id', 'review_code']
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.review_code} - {self.title}"
