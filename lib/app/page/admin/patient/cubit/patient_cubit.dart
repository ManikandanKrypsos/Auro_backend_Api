import 'dart:async';
import 'package:bloc/bloc.dart';
import '../model/patient_model.dart';
import '../service/patient_firestore_service.dart';

part 'patient_state.dart';

class PatientCubit extends Cubit<PatientState> {
  final PatientFirestoreService _firestoreService;
  StreamSubscription<List<PatientModel>>? _patientSubscription;

  PatientCubit({PatientFirestoreService? firestoreService})
      : _firestoreService = firestoreService ?? PatientFirestoreService(),
        super(const PatientState(
          allPatients: [],
          filteredPatients: [],
          selectedTab: 0,
          searchQuery: '',
          status: PatientStatus.initial,
        )) {
    _init();
  }

  void _init() {
    emit(state.copyWith(status: PatientStatus.loading));
    
    _patientSubscription = _firestoreService.getPatientsStream().listen(
      (patients) {
        emit(state.copyWith(
          allPatients: patients,
          status: PatientStatus.loaded,
        ));
        // Re-apply filter whenever data updates
        _applyCurrentFilter();
      },
      onError: (error) {
        emit(state.copyWith(
          status: PatientStatus.error,
          errorMessage: error.toString(),
        ));
      },
    );
  }

  void selectTab(int index) {
    emit(state.copyWith(selectedTab: index));
    _applyCurrentFilter();
  }

  void search(String query) {
    emit(state.copyWith(searchQuery: query));
    _applyCurrentFilter();
  }

  void _applyCurrentFilter() {
    final filtered = state.allPatients.where((patient) {
      bool matchesTab = true;
      if (state.selectedTab == 1) {
        matchesTab = patient.category.toLowerCase() == 'new';
      } else if (state.selectedTab == 2) {
        matchesTab = patient.category.toLowerCase() == 'returning';
      } else if (state.selectedTab == 3) {
        matchesTab = patient.category.toLowerCase() == 'lead' || patient.category.toLowerCase() == 'leads';
      } else if (state.selectedTab == 4) {
        matchesTab = patient.category.toLowerCase() == 'vip';
      }

      final query = state.searchQuery.toLowerCase();
      final matchesQuery = query.isEmpty ||
          patient.name.toLowerCase().contains(query) ||
          patient.id.toLowerCase().contains(query) ||
          patient.phone.toLowerCase().contains(query);

      return matchesTab && matchesQuery;
    }).toList();

    emit(state.copyWith(filteredPatients: filtered));
  }

  @override
  Future<void> close() {
    _patientSubscription?.cancel();
    return super.close();
  }
}