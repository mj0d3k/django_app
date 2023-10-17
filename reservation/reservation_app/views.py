from django.shortcuts import render, redirect
from django.views import View
from .models import ConferenceRoom, RoomBooking
import datetime


class BaseRoomView(View):
    """
    This method helps with the proper room accessibility viewing.
    """
    def update_room_context(self):
        rooms = ConferenceRoom.objects.all()
        for room in rooms:
            reservation_dates = [reservation.date.date() for reservation in room.roombooking_set.all()]
            room.reserved = datetime.date.today() in reservation_dates
        return rooms

class AddRoomView(View):
    def get(self, request):
        return render(request, "add_room.html")

    def post(self, request):
        name = request.POST.get("room-name")
        capacity = request.POST.get("capacity")
        capacity = int(capacity) if capacity else 0
        projector = request.POST.get("projector") == "on"

        if not name:
            return render(request, "add_room.html", context={"error": "Nie podano nawy sali"})
        if capacity <= 0:
            return render(request, "add_room.html", context={"error": "Pojemność sali musi być dodatnia"})
        if ConferenceRoom.objects.filter(name=name).first():
            return render(request, "add_room.html", context={"error": "Sala o podanej nazwie istnieje"})

        ConferenceRoom.objects.create(name=name, capacity=capacity, projector_availability=projector)

        return redirect('room-list')


class RoomListView(BaseRoomView):
    def get(self, request):
        rooms = self.update_room_context()
        return render(request, "rooms.html", context={"rooms": rooms})


class DeleteRoomView(BaseRoomView):
    def get(self, request, room_id: int):
        room = ConferenceRoom.objects.get(pk=room_id)
        room.delete()

        rooms = self.update_room_context()

        return render(request, "rooms.html", context={"rooms": rooms})

# with pop up

# class DeleteRoomView(BaseRoomView):
#     def post(self, request, room_id: int):
#         room = ConferenceRoom.objects.get(pk=room_id)
#         return render(request, "delete_room.html", context={"room": room})
#
#     def get(self, request, room_id: int):
#         room = ConferenceRoom.objects.get(pk=room_id)
#         room.delete()
#
#         rooms = self.update_room_context()
#
#         return render(request, "rooms.html", context={"rooms": rooms})



class ModifyRoomView(BaseRoomView):
    def get(self, request, room_id):
        room = ConferenceRoom.objects.get(pk=room_id)
        return render(request, "modify_room.html", context={"room": room})

    def post(self, request, room_id):
        room = ConferenceRoom.objects.get(pk=room_id)
        name = request.POST.get("room-name")
        capacity = request.POST.get("capacity")
        capacity = int(capacity) if capacity else 0
        projector = request.POST.get("projector") == "on"

        if not name:
            return render(request, "modify_room.html",
                          context={"room": room, "error": "Please insert conference room name"})

        if capacity <= 0:
            return render(request, "modify_room.html",
                          context={"room": room, "error": "Please insert capacity bigger than 0"})

        if name != room.name and ConferenceRoom.objects.filter(name=name).first():
            return render(request, "modify_room.html",
                          context={"room": room, "error": "Conference room name already exists"})

        room.name = name
        room.capacity = capacity
        room.projector_availability = projector
        room.save()

        rooms = self.update_room_context()

        return render(request, "rooms.html", context={"rooms": rooms})


class RoomBookingView(BaseRoomView):
    def get(self, request, room_id):
        room = ConferenceRoom.objects.get(pk=room_id)
        reservations = room.roombooking_set.filter(date__gte=str(datetime.date.today())).order_by('date')
        return render(request, "book_room.html", context={"room": room, "reservations": reservations})

    def post(self, request, room_id):
        room = ConferenceRoom.objects.get(pk=room_id)
        comment = request.POST.get("comment")
        date = request.POST.get("reservation-date")

        reservations = room.roombooking_set.filter(date__gte=str(datetime.date.today())).order_by('date')

        if RoomBooking.objects.filter(room_id=room, date=date):
            return render(request, "book_room.html", context={"room": room, "reservations": reservations,
                                                              "error": "This room is already booked on this day"})
        if date < str(datetime.date.today()):
            return render(request, "book_room.html",
                          context={"room": room, "reservations": reservations, "error": "Date cannot be from the past"})

        RoomBooking.objects.create(room_id=room, date=date, comment=comment)
        rooms = self.update_room_context()

        return render(request, "rooms.html", context={"rooms": rooms})


class RoomDetailsView(View):
    def get(self, request, room_id):
        room = ConferenceRoom.objects.get(id=room_id)
        reservations = room.roombooking_set.filter(date__gte=str(datetime.date.today())).order_by('date')
        return render(request, "room_details.html", context={"room": room, "reservations": reservations})


class SearchView(View):
    def get(self, request):
        name = request.GET.get("room-name")
        capacity = request.GET.get("capacity")
        capacity = int(capacity) if capacity else 0
        projector = request.GET.get("projector") == "on"

        rooms = ConferenceRoom.objects.all()
        if projector:
            rooms = rooms.filter(projector_availability=projector)
        if capacity:
            rooms = rooms.filter(capacity__gte=capacity)
        if name:
            rooms.filter(name__contains=name)

        for room in rooms:
            reservation_dates = [reservation.date.date() for reservation in room.roombooking_set.all()]
            room.reserved = datetime.date.today() in reservation_dates

        return render(request, "rooms.html", context={"rooms": rooms, "date": datetime.date.today()})
