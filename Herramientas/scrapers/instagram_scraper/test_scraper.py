import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from scraper import InstagramScraper

class TestInstagramScraper(unittest.TestCase):
    @patch('instaloader.Instaloader')
    @patch('instaloader.Profile')
    def test_get_account_data(self, mock_profile, mock_instaloader):
        # Setup mock
        mock_instance = mock_profile.from_username.return_value
        mock_instance.username = "testuser"
        mock_instance.followers = 1000
        mock_instance.is_private = False
        mock_instance.is_verified = True
        
        scraper = InstagramScraper()
        data = scraper.get_account_data("testuser")
        
        self.assertEqual(data['username'], "testuser")
        self.assertEqual(data['followers'], 1000)
        self.assertFalse(data['is_private'])

    @patch('instaloader.Instaloader')
    @patch('instaloader.Profile')
    def test_get_recent_posts(self, mock_profile, mock_instaloader):
        # Setup mock posts
        now = datetime.now()
        post1 = MagicMock()
        post1.date = now - timedelta(hours=1)
        post1.likes = 10
        post1.comments = 2
        
        post2 = MagicMock()
        post2.date = now - timedelta(days=2) # Older than 1 day
        post2.likes = 5
        post2.comments = 1
        
        mock_instance = mock_profile.from_username.return_value
        mock_instance.get_posts.return_value = [post1, post2]
        
        scraper = InstagramScraper()
        # Fetch for last 1 day
        posts = scraper.get_recent_posts("testuser", 1)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['likes'], 10)

if __name__ == '__main__':
    unittest.main()
