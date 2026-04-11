part of 'staff_cubit.dart';


class StaffState {
  final List<StaffModel> allStaff;
  final List<StaffModel> filteredStaff;
  final int selectedTab; 
  final String searchQuery;

  const StaffState({
    required this.allStaff,
    required this.filteredStaff,
    required this.selectedTab,
    required this.searchQuery,
  });

  StaffState copyWith({
    List<StaffModel>? allStaff,
    List<StaffModel>? filteredStaff,
    int? selectedTab,
    String? searchQuery,
  }) {
    return StaffState(
      allStaff: allStaff ?? this.allStaff,
      filteredStaff: filteredStaff ?? this.filteredStaff,
      selectedTab: selectedTab ?? this.selectedTab,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}
