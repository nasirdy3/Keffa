from django.db import models

class FAQ(models.Model):
    """
    Frequently Asked Questions model.
    Admin can add/edit questions directly from the dashboard.
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_visible = models.BooleanField(default=True, help_text="Uncheck to hide this question from the site.")
    order = models.IntegerField(default=0, help_text="Lower numbers appear first.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
