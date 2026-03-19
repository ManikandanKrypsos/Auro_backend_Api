part of 'patient_cubit.dart';


class PatientState {
  final List<PatientModel> allPatients;
  final List<PatientModel> filteredPatients;
  final int selectedTab;
  final String searchQuery;

  const PatientState({
    required this.allPatients,
    required this.filteredPatients,
    required this.selectedTab,
    required this.searchQuery,
  });

  PatientState copyWith({
    List<PatientModel>? allPatients,
    List<PatientModel>? filteredPatients,
    int? selectedTab,
    String? searchQuery,
  }) {
    return PatientState(
      allPatients: allPatients ?? this.allPatients,
      filteredPatients: filteredPatients ?? this.filteredPatients,
      selectedTab: selectedTab ?? this.selectedTab,
      searchQuery: searchQuery ?? this.searchQuery,
    );
  }
}
