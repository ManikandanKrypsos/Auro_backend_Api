import 'package:bloc/bloc.dart';

import '../domain/model/staff_model.dart';

part 'staff_state.dart';

class StaffCubit extends Cubit<StaffState> {
  StaffCubit()
    : super(
        StaffState(
          allStaff: _initialStaff,
          filteredStaff: _initialStaff
              .where((s) => s.jobRole == StaffRole.therapist)
              .toList(),
          selectedTab: 0,
          searchQuery: '',
        ),
      );

  static const List<StaffModel> _initialStaff = [
    StaffModel(
      name: 'ELENA STERLING',
      role: 'Senior Wellness Therapist',
      rating: '4.9',
      experience: '6Y EXPERIENCE',
      status: StaffStatus.active,
      jobRole: StaffRole.therapist,
      image: 'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    ),
    StaffModel(
      name: 'MARCUS VANE',
      role: 'Lead Aesthetician',
      rating: '5.0',
      experience: '12Y EXPERIENCE',
      status: StaffStatus.onLeave,
      jobRole: StaffRole.therapist,
      image: 'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    ),
    StaffModel(
      name: 'SIENNA THORNE',
      role: 'Dermal Clinician',
      rating: '4.8',
      experience: '5Y EXPERIENCE',
      status: StaffStatus.active,
      jobRole: StaffRole.therapist,
      image: 'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    ),
    StaffModel(
      name: 'ARIA MOON',
      role: 'Front Desk Coordinator',
      rating: '4.7',
      experience: '3Y EXPERIENCE',
      status: StaffStatus.active,
      jobRole: StaffRole.receptionist,
      image: 'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    ),
    StaffModel(
      name: 'JAMES FORD',
      role: 'Client Relations',
      rating: '4.6',
      experience: '2Y EXPERIENCE',
      status: StaffStatus.active,
      jobRole: StaffRole.receptionist,
      image: 'https://i.pinimg.com/1200x/6c/59/95/6c599523460f54ddeba81f3cd689ae04.jpg',
    ),
  ];

  // ── filter logic lives here, UI knows nothing about it ──
  void selectTab(int index) {
    final role = index == 0 ? StaffRole.therapist : StaffRole.receptionist;
    emit(
      state.copyWith(
        selectedTab: index,
        filteredStaff: _applyFilter(role: role, query: state.searchQuery),
      ),
    );
  }

  void search(String query) {
    final role = state.selectedTab == 0
        ? StaffRole.therapist
        : StaffRole.receptionist;
    emit(
      state.copyWith(
        searchQuery: query,
        filteredStaff: _applyFilter(role: role, query: query),
      ),
    );
  }

  List<StaffModel> _applyFilter({
    required StaffRole role,
    required String query,
  }) {
    return state.allStaff.where((staff) {
      final matchesRole = staff.jobRole == role;
      final matchesQuery =
          query.isEmpty ||
          staff.name.toLowerCase().contains(query.toLowerCase()) ||
          staff.role.toLowerCase().contains(query.toLowerCase());
      return matchesRole && matchesQuery;
    }).toList();
  }
}
