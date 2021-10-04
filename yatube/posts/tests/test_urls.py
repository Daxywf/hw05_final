from http import HTTPStatus

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
CREATE_URL = reverse('posts:post_create')
UNEXISTING_URL = '/unexisting_page/'
PROFILE_URL = reverse(
    'posts:profile',
    kwargs={'username': 'test_profile'}
)
GROUP_URL = reverse(
    'posts:group_posts',
    kwargs={'slug': 'test-slug'}
)
AUTH_TO_CREATE_URL = f'{settings.LOGIN_URL}?next={CREATE_URL}'


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
        )
        cls.author = User.objects.create(
            username='test_profile'
        )
        cls.not_author1 = User.objects.create(
            username='test_profile2',
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.author
        )
        cls.POST_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POSTS_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.AUTH_TO_EDIT_URL = (f'{settings.LOGIN_URL}'
                                f'?next={cls.POSTS_EDIT_URL}')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.not_author = Client()
        self.not_author.force_login(self.not_author1)

    def test_pages_responses(self):
        pages = [
            [INDEX_URL, Client(), HTTPStatus.OK],
            [GROUP_URL, Client(), HTTPStatus.OK],
            [self.POST_URL, Client(), HTTPStatus.OK],
            [PROFILE_URL, Client(), HTTPStatus.OK],
            [UNEXISTING_URL, Client(), HTTPStatus.NOT_FOUND],
            [CREATE_URL, Client(), HTTPStatus.FOUND],
            [CREATE_URL, self.not_author, HTTPStatus.OK],
            [self.POSTS_EDIT_URL, Client(), HTTPStatus.FOUND],
            [
                self.POSTS_EDIT_URL,
                self.not_author,
                HTTPStatus.FOUND
            ],
            [
                self.POSTS_EDIT_URL,
                self.authorized_client,
                HTTPStatus.OK
            ]
        ]
        for adress, client, status in pages:
            self.assertEqual(
                client.get(adress).status_code, status
            )

    def test_urls_use_correct_templates(self):
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            PROFILE_URL: 'posts/profile.html',
            GROUP_URL: 'posts/group_list.html',
            self.POST_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/create_post.html',
            self.POSTS_EDIT_URL: 'posts/create_post.html',
            FOLLOW_URL: 'posts/follow.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                cache.clear()
                self.assertTemplateUsed(
                    self.authorized_client.get(adress),
                    template
                )

    def test_redirects(self):
        redirects = [
            [
                CREATE_URL,
                Client(),
                AUTH_TO_CREATE_URL
            ],
            [
                self.POSTS_EDIT_URL,
                Client(),
                self.AUTH_TO_EDIT_URL
            ],
            [
                self.POSTS_EDIT_URL,
                self.not_author,
                self.POST_URL
            ]
        ]
        for url, client, redirect_url in redirects:
            self.assertRedirects(
                client.get(url, follow=True),
                redirect_url
            )
