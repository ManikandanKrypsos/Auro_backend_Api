part of 'patient_detail_cubit.dart';

class PatientDetailState {
  final int selectedTab;
 
  const PatientDetailState({required this.selectedTab});
 
  PatientDetailState copyWith({int? selectedTab}) =>
      PatientDetailState(selectedTab: selectedTab ?? this.selectedTab);
}
