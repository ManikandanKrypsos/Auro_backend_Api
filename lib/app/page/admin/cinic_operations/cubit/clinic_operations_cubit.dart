import 'package:bloc/bloc.dart';
import 'package:flutter/material.dart';

part 'clinic_operations_state.dart';



class ClinicOperationsCubit extends Cubit<ClinicOperationsState> {
  ClinicOperationsCubit() : super(const ClinicOperationsState());

  void toggleDay(String day) {
    final updated = Map<String, ClinicDaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(enabled: !updated[day]!.enabled);
    emit(state.copyWith(weekSchedule: updated));
  }

  void setOpenTime(String day, TimeOfDay time) {
    final updated = Map<String, ClinicDaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(openTime: time);
    emit(state.copyWith(weekSchedule: updated));
  }

  void setCloseTime(String day, TimeOfDay time) {
    final updated = Map<String, ClinicDaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(closeTime: time);
    emit(state.copyWith(weekSchedule: updated));
  }

  void addClosure(ClinicClosure closure) =>
      emit(state.copyWith(closures: [...state.closures, closure]));

  void removeClosure(int index) {
    final updated = List<ClinicClosure>.from(state.closures)..removeAt(index);
    emit(state.copyWith(closures: updated));
  }
}
