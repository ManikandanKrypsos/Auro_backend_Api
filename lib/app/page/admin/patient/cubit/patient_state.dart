part of 'patient_cubit.dart';

enum PatientStatus { initial, loading, loaded, error }

class PatientState {
  final List<PatientModel> allPatients;
  final List<PatientModel> filteredPatients;
  final int selectedTab;
  final String searchQuery;
  final PatientStatus status;
  final String errorMessage;

  const PatientState({
    required this.allPatients,
    required this.filteredPatients,
    required this.selectedTab,
    required this.searchQuery,
    this.status = PatientStatus.initial,
    this.errorMessage = '',
  });

  PatientState copyWith({
    List<PatientModel>? allPatients,
    List<PatientModel>? filteredPatients,
    int? selectedTab,
    String? searchQuery,
    PatientStatus? status,
    String? errorMessage,
  }) {
    return PatientState(
      allPatients: allPatients ?? this.allPatients,
      filteredPatients: filteredPatients ?? this.filteredPatients,
      selectedTab: selectedTab ?? this.selectedTab,
      searchQuery: searchQuery ?? this.searchQuery,
      status: status ?? this.status,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}
