
from datetime import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from Restaurant.models import Restaurant
from .models import Post, GroupTraits, PostImage
from .serializers import PostSerializer,GroupTraitsSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes

@api_view(['POST'])  # POST 메소드만 허용
@permission_classes((IsAuthenticated, ))
@authentication_classes([JWTAuthentication])
@api_view(['POST'])
def create_post(request):
    if request.method == 'POST':
        data = request.data
        
        restaurant_id = data.pop('restaurant')  # 사용자가 선택한 레스토랑의 ID
        
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)  # 선택한 레스토랑 정보 가져오기
        
        group_traits_data = data.pop('group_traits')
        images = request.FILES.getlist('images')
        
        # User 정보 가져오기
        user = request.user
        
        # Post 모델에 필요한 데이터 설정
        data['user'] = user.id  # 로그인한 사용자의 ID를 사용하여 user 필드 설정
        data['isManager'] = True  # 생성하는 사용자는 매니저이므로 True로 설정
        data['createdAt'] = timezone.now()  # 현재 시간으로 설정
        
        # Post 생성 진행
        post_serializer = PostSerializer(data=data)
        if post_serializer.is_valid():
            post_instance = post_serializer.save(restaurant=restaurant)
            
            # GroupTraits 정보 저장
            group_traits_data['post'] = post_instance.pk
            group_traits_serializer = GroupTraitsSerializer(data=group_traits_data)
            if group_traits_serializer.is_valid():
                group_traits_serializer.save()
            else:
                post_instance.delete()
                return Response(group_traits_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # 여러 개의 이미지 업로드 처리
            for image in images:
                PostImage.objects.create(post=post_instance, image=image)
            
            return Response({'message': 'Post and GroupTraits created successfully'}, status=status.HTTP_201_CREATED)
        
        return Response(post_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
@authentication_classes([JWTAuthentication])
def join_post(request, post_id):
    if request.method == 'POST':
        user = request.user  # 현재 로그인한 사용자
        
        post = get_object_or_404(Post, id=post_id)
        
        if user == post.user:
            return Response({'message': 'You cannot join your own post'}, status=status.HTTP_400_BAD_REQUEST)
        
        if post.number <= 0:
            return Response({'message': 'This post is already full'}, status=status.HTTP_400_BAD_REQUEST)
        
        post.participants.add(user)
        post.number -= 1
        post.save()
        
        return Response({'message': 'Joined the post successfully'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_all_posts(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=200)


@api_view(['GET'])
def get_post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    serializer = PostSerializer(post)
    return Response(serializer.data, status=200)