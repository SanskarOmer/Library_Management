from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from library.models import Transaction

class Command(BaseCommand):
    help = 'Clean up any existing transactions for admin users'

    def handle(self, *args, **options):
        # Find all transactions for staff users
        admin_transactions = Transaction.objects.filter(user__is_staff=True)
        count = admin_transactions.count()
        
        if count > 0:
            self.stdout.write(
                self.style.WARNING(f'Found {count} transactions for admin users. These will be deleted.')
            )
            
            # Return books to available stock before deleting transactions
            for tx in admin_transactions:
                if tx.status == 'issued':
                    book = tx.book
                    book.available_copies += 1
                    if book.available_copies > book.total_copies:
                        book.available_copies = book.total_copies
                    book.save()
                    self.stdout.write(f'Returned book: {book.title}')
            
            # Delete the transactions
            admin_transactions.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {count} admin transactions.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No admin transactions found. Database is clean.')
            )